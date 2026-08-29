<template>
  <div class="app-shell">
    <AppSidebar :active-section="activeSection" @navigate="handleNavigation" />
    <div class="app-main">
      <TopBar />
      <TaskWorkbench
        v-if="activeSection === 'tasks'"
        :task="task"
        :objective="objective"
        :active-tab="activeTab"
        :busy="busy"
        :events="events"
        :error-message="errorMessage"
        @update:objective="objective = $event"
        @update:active-tab="activeTab = $event"
        @execute="executeTask"
        @review="submitReview"
        @new-task="createDraft(scenario)"
      />
      <KnowledgeBasePage v-else-if="activeSection === 'knowledge'" :categories="systemCatalog.knowledge || []" />
      <TestCenterPage
        v-else
        :tests="systemCatalog.tests || []"
        :agents="systemCatalog.agents || []"
        :verification="systemCatalog.verification || {}"
        :runtime="systemCatalog.runtime || 'deterministic'"
        @run-case="runTestCase"
      />
    </div>

    <nav class="mobile-nav" aria-label="移动导航">
      <button
        v-for="item in mobileNavigation"
        :key="item.id"
        type="button"
        :class="{ active: activeSection === item.id }"
        @click="handleNavigation(item.id)"
      >
        <component :is="item.icon" :size="20" weight="regular" />
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <transition name="toast">
      <div v-if="toast" class="toast" role="status">{{ toast }}</div>
    </transition>
  </div>
</template>

<script setup>
import { markRaw, onBeforeUnmount, onMounted, ref } from 'vue';
import { PhFlask as Flask, PhFolderSimple as FolderSimple, PhNotebook as Notebook } from '@phosphor-icons/vue';
import AppSidebar from './components/AppSidebar.vue';
import TopBar from './components/TopBar.vue';
import TaskWorkbench from './components/TaskWorkbench.vue';
import KnowledgeBasePage from './components/KnowledgeBasePage.vue';
import TestCenterPage from './components/TestCenterPage.vue';
import { connectOfflineTask, isOfflineMode, offlineRequest } from './offline-runtime.js';

const DEFAULT_OBJECTIVE = '提升高流失高客单用户 30 天复购率 5%';
const task = ref(null);
const objective = ref(DEFAULT_OBJECTIVE);
const activeTab = ref('sql');
const activeSection = ref('tasks');
const scenario = ref('normal');
const busy = ref(false);
const events = ref([]);
const errorMessage = ref('');
const toast = ref('');
const systemCatalog = ref({ knowledge: [], tests: [], agents: [], verification: {} });
let eventSource = null;

const mobileNavigation = [
  { id: 'tasks', label: '任务', icon: markRaw(FolderSimple) },
  { id: 'knowledge', label: '知识库', icon: markRaw(Notebook) },
  { id: 'tests', label: '测试', icon: markRaw(Flask) },
];

function showToast(message) {
  toast.value = message;
  window.setTimeout(() => {
    if (toast.value === message) toast.value = '';
  }, 2600);
}

async function request(path, options = {}) {
  if (isOfflineMode) return offlineRequest(path, options);
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || '服务暂时不可用');
  }
  return response.json();
}

async function createDraft(mode = 'normal') {
  closeStream();
  busy.value = true;
  errorMessage.value = '';
  events.value = [];
  scenario.value = mode;
  try {
    task.value = await request('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ prompt: objective.value, scenario: mode }),
    });
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    busy.value = false;
  }
}

async function loadSystemCatalog() {
  try {
    systemCatalog.value = await request('/api/system');
  } catch (error) {
    errorMessage.value = `系统目录加载失败：${error.message}`;
  }
}

async function executeTask() {
  if (busy.value || !objective.value.trim()) return;
  if (!task.value || task.value.status !== 'draft' || task.value.prompt !== objective.value) {
    await createDraft(scenario.value);
  }
  if (!task.value) return;
  busy.value = true;
  errorMessage.value = '';
  try {
    task.value = await request(`/api/tasks/${task.value.id}/confirm`, { method: 'POST' });
    connectStream(task.value.id);
  } catch (error) {
    busy.value = false;
    errorMessage.value = error.message;
  }
}

function connectStream(taskId) {
  closeStream();
  if (isOfflineMode) {
    eventSource = connectOfflineTask(
      taskId,
      (event) => handleTaskEvent(taskId, event),
      () => {
        errorMessage.value = '离线演示运行失败，请重新运行任务';
        busy.value = false;
      },
    );
    return;
  }
  eventSource = new EventSource(`/api/tasks/${taskId}/events`);
  eventSource.onmessage = async (message) => {
    const event = JSON.parse(message.data);
    await handleTaskEvent(taskId, event);
  };
  eventSource.onerror = async () => {
    try {
      task.value = await request(`/api/tasks/${taskId}`);
      if (!['awaiting_review', 'completed', 'rejected', 'failed'].includes(task.value.status)) {
        errorMessage.value = '执行记录连接已中断，请重新运行任务';
      }
    } catch {
      errorMessage.value = '无法连接 ReGrow 后端服务';
    }
    busy.value = false;
    closeStream();
  };
}

async function handleTaskEvent(taskId, event) {
  if (!events.value.some((item) => item.sequence === event.sequence)) events.value.push(event);
  task.value = await request(`/api/tasks/${taskId}`);
  if (['completed', 'rejected', 'failed'].includes(task.value.status)) {
    busy.value = false;
    closeStream();
    showToast(task.value.status === 'completed' ? '任务完成，实验方案已生成' : '任务已停止');
  } else if (task.value.status === 'awaiting_review') {
    busy.value = false;
  }
}

async function submitReview(action) {
  if (!task.value) return;
  busy.value = true;
  try {
    await request(`/api/tasks/${task.value.id}/review`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        comment: action === 'approve' ? '同意先行灰度验证' : '需要缩小范围后重试',
      }),
    });
    connectStream(task.value.id);
  } catch (error) {
    errorMessage.value = error.message;
    busy.value = false;
  }
}

function handleNavigation(section) {
  activeSection.value = section;
  if (section === 'tasks') {
    scenario.value = 'normal';
    objective.value = DEFAULT_OBJECTIVE;
    createDraft('normal');
  } else {
    showToast(section === 'knowledge' ? '已打开当前任务使用的知识库' : '已打开测试中心');
  }
}

async function runTestCase(testCase) {
  activeSection.value = 'tasks';
  scenario.value = testCase.scenario;
  activeTab.value = testCase.focus_tab;
  objective.value = testCase.id === 'guardrail'
    ? '针对高价值流失客群执行 55,000 人批量召回，验证人工审核和工作流恢复'
    : DEFAULT_OBJECTIVE;
  await createDraft(testCase.scenario);
  showToast(`正在运行：${testCase.name}`);
  await executeTask();
}

function closeStream() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

onMounted(() => Promise.all([createDraft('normal'), loadSystemCatalog()]));
onBeforeUnmount(closeStream);
</script>
