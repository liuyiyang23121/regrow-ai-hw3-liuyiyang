<template>
  <div class="assets-container">
    <!-- 资产卡片 1：数据工程与 SQL 沉淀 -->
    <div class="asset-card">
      <div class="card-header">
        <span class="icon">📊</span>
        <h3>核心数据资产：清洗规则与生产级 SQL 脚本</h3>
      </div>
      <div class="card-body code-mode">
        <pre v-if="sqlCode"><code>{{ sqlCode }}</code></pre>
        <div v-else class="placeholder-text">
          等待数据工程智能体激活并输出流式 SQL 代码...
        </div>
      </div>
    </div>

    <!-- 资产卡片 2：市场策略文案 -->
    <div class="asset-card">
      <div class="card-header">
        <span class="icon">🎯</span>
        <h3>业务策略资产：精准客群营销文案</h3>
      </div>
      <div class="card-body text-mode">
        <div v-if="marketingText" class="text-content">
          {{ marketingText }}
        </div>
        <div v-else class="placeholder-text">
          等待营销策略智能体完成分析并生成触达文案...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sqlCode: {
    type: String,
    default: ''
  },
  marketingText: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.assets-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.asset-card {
  background-color: #111827;
  border: 1px solid #1e293b;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex: 1; /* 高度平分 */
  min-height: 0;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid #1e293b;
  background-color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 {
  margin: 0;
  font-size: 0.9rem;
  color: #f1f5f9;
  font-weight: 600;
}

.icon { font-size: 1.1rem; }

.card-body {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  font-size: 0.88rem;
  line-height: 1.6;
}

.code-mode {
  background-color: #05070a;
  color: #34d399;
  font-family: "Fira Code", monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.code-mode pre {
  margin: 0;
}

.text-mode {
  color: #e2e8f0;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-all;
}

.placeholder-text {
  color: #4b5563;
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 0.85rem;
}
</style>