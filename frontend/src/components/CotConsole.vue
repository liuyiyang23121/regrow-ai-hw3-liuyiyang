<template>
  <section class="console-section">
    <div class="panel-header">
      <div class="header-left">
        <span class="terminal-icon">🖲️</span>
        <h3>多智能体对抗自学习协同矩阵 (CoT Panel)</h3>
      </div>
      <span v-if="isRunning" class="pulse-dot"></span>
    </div>
    
    <div class="console-body" ref="consoleRef">
      <div 
        v-for="(log, index) in logs" 
        :key="index" 
        :class="['log-block', log.type || log.event]"
      >
        <!-- 系统级硬事件拦截信号 -->
        <div v-if="log.event" class="event-line">
          <span class="text-content">{{ log.content }}</span>
        </div>
        
        <!-- 聚合后的智能体丝滑打字机块 -->
        <div v-else class="agent-stream-block">
          <div class="agent-meta">
            <span class="badge agent-tag">@{{ log.agent }}</span>
            <span class="status-indicator">正在深度思考...</span>
          </div>
          <div class="agent-content-body">
            <span class="text-content">{{ log.content }}</span>
          </div>
        </div>
      </div>
      
      <!-- 兜底状态 -->
      <div v-if="logs.length === 0" class="empty-holder">
        <div class="radar"></div>
        <p>等待多智能体编排链路启动，暂无实时思维流...</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  logs: { type: Array, required: true, default: () => [] },
  isRunning: { type: Boolean, default: false }
});

const consoleRef = ref(null);

watch(
  () => props.logs,
  async () => {
    await nextTick();
    if (consoleRef.value) {
      // 增加平滑触底滚动体验
      consoleRef.value.scrollTo({
        top: consoleRef.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  },
  { deep: true }
);
</script>

<style scoped>
.console-section {
  flex: 1;
  background-color: #0b0f17;
  border: 1px solid #1e293b;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #1e293b;
  background-color: #111827;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.terminal-icon { font-size: 1rem; color: #38bdf8; }

.panel-header h3 {
  margin: 0;
  font-size: 0.9rem;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #34d399;
  border-radius: 50%;
  box-shadow: 0 0 10px #34d399;
  animation: pulse 1.8s infinite;
}

.console-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  font-family: "Fira Code", "Courier New", monospace;
  font-size: 0.86rem;
  line-height: 1.7;
}

.log-block {
  margin-bottom: 18px;
  animation: fadeIn 0.2s ease-out;
}

/* 智能体聚合卡片样式 */
.agent-stream-block {
  background: rgba(30, 41, 59, 0.3);
  border-left: 3px solid #3b82f6;
  padding: 10px 14px;
  border-radius: 4px;
}

.agent-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.badge.agent-tag {
  background-color: #2563eb;
  color: #ffffff;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.status-indicator {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

.agent-content-body {
  color: #cbd5e1;
}

/* 系统信号线样式 */
.event-line {
  color: #38bdf8;
  background-color: rgba(56, 189, 248, 0.1);
  border: 1px dashed rgba(56, 189, 248, 0.3);
  padding: 8px 12px;
  border-radius: 6px;
  text-align: center;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-all;
}

.empty-holder {
  color: #4b5563;
  text-align: center;
  padding-top: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(2px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.5; }
}
</style>