<template>
  <main class="section-page test-center-page">
    <header class="section-page-header">
      <div>
        <div class="section-eyebrow"><Flask :size="16" /> 运行检查</div>
        <h1>自动化测试</h1>
        <p>三个用例分别检查正常任务、SQL 修复和大客群审核。点击卡片即可用相同数据重新运行。</p>
      </div>
      <div class="test-pass-summary"><CheckCircle :size="20" weight="fill" /><div><strong>{{ verification.passed || 0 }}/{{ verification.automated_tests || 0 }} 自动化测试通过</strong><span>上次运行 {{ verification.last_verified || '—' }}</span></div></div>
    </header>

    <section class="test-case-grid" aria-label="核心测试用例">
      <article v-for="item in tests" :key="item.id" class="test-case-card">
        <header><span :class="['case-icon', item.id]"><component :is="caseIcon(item.id)" :size="20" /></span><span class="case-status"><Check :size="13" /> 已通过</span></header>
        <h2>{{ item.name }}</h2><p>{{ item.description }}</p>
        <dl><dt>通过条件</dt><dd>{{ item.expected }}</dd></dl>
        <button type="button" class="button-secondary" @click="$emit('run-case', item)"><Play :size="15" weight="fill" /> 运行用例</button>
      </article>
    </section>

    <section class="agent-panel">
      <header><div><h2>多智能体协作链路</h2><p>模型负责理解和生成，工具负责查数，护栏决定是否放行。</p></div><span>运行模式：{{ runtime === 'agno' ? 'Agno' : '固定演示数据' }}</span></header>
      <ol class="agent-chain">
        <li v-for="(agent, index) in agents" :key="agent.name"><span>{{ index + 1 }}</span><div><strong>{{ agent.name }}</strong><small>{{ agent.role }}</small></div><CaretRight v-if="index < agents.length - 1" :size="15" /></li>
      </ol>
    </section>
  </main>
</template>

<script setup>
import {
  PhArrowsClockwise as ArrowsClockwise, PhCaretRight as CaretRight, PhCheck as Check, PhCheckCircle as CheckCircle,
  PhFlask as Flask, PhPlay as Play, PhShieldWarning as ShieldWarning, PhStack as Stack,
} from '@phosphor-icons/vue';

defineProps({
  tests: { type: Array, default: () => [] }, agents: { type: Array, default: () => [] },
  verification: { type: Object, default: () => ({}) }, runtime: { type: String, default: 'deterministic' },
});
defineEmits(['run-case']);
function caseIcon(id) { return id === 'sql_repair' ? ArrowsClockwise : id === 'guardrail' ? ShieldWarning : Stack; }
</script>
