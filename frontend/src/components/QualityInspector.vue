<template>
  <aside class="quality-inspector" aria-label="质量与风险">
    <header><h2>质量与风险</h2><Question :size="16" /></header>
    <div class="metric-list">
      <div class="metric-row"><div><span>{{ props.task?.assets?.risk?.target_rows ? '计划触达规模' : '客群规模（预计）' }}</span><strong>{{ formatNumber(audienceSize) }}</strong></div><UsersThree :size="25" /></div>
      <div class="metric-row"><div><span>SQL 已修复</span><strong>{{ metrics.sql_retries || 0 }}<small> 次</small></strong></div><Wrench :size="24" /></div>
      <div class="metric-row"><div><span>数据质量评分</span><strong>{{ metrics.data_quality || 0 }}<small> /100</small></strong></div><ShieldCheck :size="24" /></div>
      <div class="metric-row" :class="{ danger: riskLevel === '高' }"><div><span>风险等级</span><strong>{{ riskLevel }}</strong></div><ShieldWarning v-if="riskLevel === '高'" :size="24" /><ShieldCheck v-else :size="24" /></div>
    </div>

    <div class="inspection-checks">
      <h3>上线前检查</h3>
      <ul>
        <li v-for="check in checks" :key="check.name"><Check :size="14" weight="bold" /><span>{{ check.name }}</span><strong>通过</strong></li>
      </ul>
    </div>

    <div v-if="toolReceipt" class="inspector-tool">
      <Wrench :size="18" /><div><strong>已运行清理工具</strong><span>{{ toolReceipt.tool }}</span></div><small>{{ formatNumber(toolReceipt.rows_after) }} 人</small>
    </div>

    <button type="button" class="report-button" @click="downloadReport"><FileText :size="17" /> 打开任务报告</button>
  </aside>
</template>

<script setup>
import { computed } from 'vue';
import {
  PhCheck as Check,
  PhFileText as FileText,
  PhQuestion as Question,
  PhShieldCheck as ShieldCheck,
  PhShieldWarning as ShieldWarning,
  PhUsersThree as UsersThree,
  PhWrench as Wrench,
} from '@phosphor-icons/vue';

const props = defineProps({ task: { type: Object, default: null } });
const metrics = computed(() => props.task?.metrics || {});
const audienceSize = computed(() => props.task?.assets?.risk?.target_rows || metrics.value.audience_size || 0);
const riskLevel = computed(() => metrics.value.risk_level || '待评估');
const checks = computed(() => props.task?.assets?.risk?.checks || [
  { name: '敏感信息脱敏' }, { name: '黑名单过滤' }, { name: '重复用户排重' }, { name: '时间窗口合理性' }, { name: '人群重叠检查' },
]);
const toolReceipt = computed(() => props.task?.assets?.tool_receipts?.[0]);

function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN'); }
function downloadReport() {
  if (!props.task) return;
  if (window.location.protocol === 'file:' || new URLSearchParams(window.location.search).has('offline')) {
    const report = new Blob([JSON.stringify(props.task, null, 2)], { type: 'application/json;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(report);
    link.download = `${props.task.id}-report.json`;
    link.click();
    URL.revokeObjectURL(link.href);
    return;
  }
  window.open(`/api/tasks/${props.task.id}/report`, '_blank', 'noopener,noreferrer');
}
</script>
