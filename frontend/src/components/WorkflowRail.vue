<template>
  <ol class="workflow-rail" aria-label="任务执行进度">
    <li v-for="(node, index) in nodes" :key="node.id" :class="node.status">
      <div class="step-line" aria-hidden="true"></div>
      <div class="step-marker">
        <Check v-if="node.status === 'completed'" :size="15" weight="bold" />
        <Warning v-else-if="node.status === 'blocked' || node.status === 'failed'" :size="15" weight="fill" />
        <span v-else>{{ index + 1 }}</span>
      </div>
      <div class="step-copy">
        <strong>{{ node.name }}</strong>
        <span>{{ statusLabel(node) }}</span>
      </div>
    </li>
  </ol>
</template>

<script setup>
import { PhCheck as Check, PhWarning as Warning } from '@phosphor-icons/vue';

defineProps({ nodes: { type: Array, required: true } });

function statusLabel(node) {
  const labels = {
    pending: '待处理', running: '进行中', completed: '已完成', blocked: '待审核', failed: '已停止',
  };
  return labels[node.status] || '待处理';
}
</script>
