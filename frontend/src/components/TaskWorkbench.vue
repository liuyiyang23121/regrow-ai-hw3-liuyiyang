<template>
  <main class="task-page">
    <div class="task-title-row">
      <div class="task-heading"><h1>高价值用户召回 <PencilSimple :size="20" weight="regular" /></h1></div>
      <button type="button" class="button-primary execute-button" :disabled="busy || !objective.trim()" @click="$emit('execute')">
        <SpinnerGap v-if="busy" :size="18" class="spin" />
        <Play v-else :size="18" weight="fill" />
        {{ actionLabel }}
      </button>
    </div>

    <div class="objective-editor">
      <label for="objective">目标（可编辑）</label>
      <div class="objective-input">
        <input id="objective" :value="objective" :disabled="isLocked" maxlength="100" @input="$emit('update:objective', $event.target.value)" />
        <span>{{ objective.length }}/100</span>
        <PencilSimple :size="18" />
      </div>
    </div>

    <div v-if="errorMessage" class="error-banner" role="alert"><WarningCircle :size="18" />{{ errorMessage }}</div>
    <WorkflowRail :nodes="nodes" />

    <div class="work-area">
      <AssetWorkspace :task="task" :active-tab="activeTab" :events="events" @update:active-tab="$emit('update:active-tab', $event)" />
      <div class="right-column">
        <QualityInspector :task="task" />
        <section v-if="task?.status === 'awaiting_review'" class="review-panel" aria-live="polite">
          <div class="review-heading"><Warning :size="22" weight="fill" /><div><h2>需要人工审核</h2><p>计划触达人数超过 50,000，任务已暂停。请确认是否继续。</p></div></div>
          <dl><div><dt>计划触达</dt><dd>{{ formatNumber(task.assets.risk?.target_rows) }} 人</dd></div><div><dt>风险等级</dt><dd>高</dd></div></dl>
          <div class="review-actions">
            <button type="button" class="button-secondary danger" @click="$emit('review', 'reject')">驳回并结束</button>
            <button type="button" class="button-primary small" @click="$emit('review', 'approve')">批准并继续</button>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue';
import {
  PhPencilSimple as PencilSimple,
  PhPlay as Play,
  PhSpinnerGap as SpinnerGap,
  PhWarning as Warning,
  PhWarningCircle as WarningCircle,
} from '@phosphor-icons/vue';
import AssetWorkspace from './AssetWorkspace.vue';
import QualityInspector from './QualityInspector.vue';
import WorkflowRail from './WorkflowRail.vue';

const props = defineProps({
  task: { type: Object, default: null }, objective: { type: String, required: true }, activeTab: { type: String, required: true },
  busy: { type: Boolean, default: false }, events: { type: Array, default: () => [] }, errorMessage: { type: String, default: '' },
});
defineEmits(['update:objective', 'update:active-tab', 'execute', 'review', 'new-task']);

const defaultNodes = ['目标解析', '客群圈选', 'SQL 验证', '数据清洗', 'A/B 文案', '安全审核'].map((name, index) => ({ id: String(index), name, status: 'pending' }));
const nodes = computed(() => props.task?.nodes || defaultNodes);
const isLocked = computed(() => ['running', 'awaiting_review'].includes(props.task?.status));
const actionLabel = computed(() => {
  if (props.busy || props.task?.status === 'running') return '确认并执行';
  if (props.task?.status === 'awaiting_review') return '等待审核';
  if (['completed', 'rejected', 'failed'].includes(props.task?.status)) return '重新运行';
  return '确认并执行';
});
function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN'); }
</script>
