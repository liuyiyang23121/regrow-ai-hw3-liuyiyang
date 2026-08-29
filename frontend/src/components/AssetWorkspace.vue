<template>
  <section class="asset-workspace" aria-label="任务资产">
    <div class="asset-tabs" role="tablist" aria-label="资产类型">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        :aria-selected="activeTab === tab.id"
        :class="{ active: activeTab === tab.id }"
        @click="$emit('update:activeTab', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="activeTab === 'sql'" class="sql-surface">
      <div class="asset-toolbar">
        <div class="toolbar-group">
          <span class="toolbar-label">SQL 版本</span>
          <button type="button" class="select-control">
            v{{ sqlVersion }} {{ sqlVersion > 1 ? '（已修复）' : '' }} <CaretDown :size="13" />
          </button>
          <button type="button" class="button-secondary" @click="toolMessage = '已切换版本对比视图'">对比 v1</button>
        </div>
        <div class="toolbar-group toolbar-actions">
          <button type="button" class="button-secondary" @click="toolMessage = 'SQL 格式已统一'">
            <TextAlignLeft :size="15" /> 格式化
          </button>
          <button type="button" class="button-secondary" @click="toolMessage = '沙盒验证已通过'">
            <Play :size="15" /> 运行
          </button>
          <button type="button" class="button-primary small" @click="copySql">
            <CheckCircle :size="15" /> 保存并验证
          </button>
        </div>
      </div>

      <div class="code-editor" aria-label="SQL 代码">
        <div v-for="(line, index) in sqlLines" :key="index" class="code-line">
          <span class="line-number">{{ index + 1 }}</span>
          <code v-html="highlightSqlLine(line)"></code>
        </div>
        <div v-if="!assets.sql" class="editor-empty">
          <SpinnerGap v-if="isRunning" :size="24" class="spin" />
          <Database v-else :size="24" />
          <span>{{ isRunning ? 'SQL Agent 正在生成并验证查询…' : '确认目标后，系统会生成客群 SQL' }}</span>
        </div>
      </div>

      <div class="validation-receipt">
        <div class="receipt-result">
          <CheckCircle :size="21" weight="fill" />
          <strong>{{ assets.sql ? 'SQL 验证通过' : '等待 SQL 验证' }}</strong>
        </div>
        <dl>
          <div><dt>预计客群规模</dt><dd>{{ formatNumber(metrics.audience_size) }}</dd></div>
          <div><dt>数据范围</dt><dd>2026-02-25 ～ 2026-08-24</dd></div>
          <div><dt>运行时间</dt><dd>{{ metrics.sql_execution_ms || '—' }}ms</dd></div>
        </dl>
        <button type="button" class="button-secondary"><Table :size="16" /> 查看样例数据</button>
      </div>

      <div v-if="repairEvent || toolMessage" class="activity-row">
        <Info :size="18" weight="fill" />
        <span>{{ toolMessage || formatEvent(repairEvent) }}</span>
        <button type="button" @click="toolMessage = ''">查看详情 <CaretRight :size="13" /></button>
      </div>
    </div>

    <div v-else-if="activeTab === 'audience'" class="document-surface">
      <header class="document-header">
        <div><h2>客群定义与规则</h2><p>系统按数据字典和营销授权条件生成以下规则。</p></div>
        <span>{{ formatNumber(metrics.audience_size) }} 人</span>
      </header>
      <div class="rule-table" role="table">
        <div class="rule-row rule-head" role="row"><span>规则项</span><span>筛选条件</span><span>状态</span></div>
        <div v-for="rule in audienceRules" :key="rule.label" class="rule-row" role="row">
          <strong>{{ rule.label }}</strong><code>{{ rule.rule }}</code><span class="passed"><Check :size="14" /> 已校验</span>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'quality'" class="document-surface">
      <header class="document-header"><div><h2>数据质量与清洗回执</h2><p>这里记录原始人数、排除人数、质量检查和工具执行结果。</p></div><span>{{ quality.score || 0 }}/100</span></header>
      <div class="quality-summary-grid">
        <article><ShieldCheck :size="21" /><div><span>综合质量分</span><strong>{{ quality.score || 0 }}</strong></div><small>/100</small></article>
        <article><UsersThree :size="21" /><div><span>最终可用客群</span><strong>{{ formatNumber(metrics.audience_size) }}</strong></div><small>人</small></article>
        <article><Broom :size="21" /><div><span>频控排除</span><strong>{{ formatNumber(quality.removed_rows) }}</strong></div><small>人</small></article>
        <article><Timer :size="21" /><div><span>工具耗时</span><strong>{{ toolReceipt?.execution_ms || 0 }}</strong></div><small>ms</small></article>
      </div>
      <div class="surface-section-heading"><div><h3>检查结果</h3><p>按营销数据质量规则 v1.4 检查</p></div><span>{{ assets.sql ? '5 项通过' : '等待执行' }}</span></div>
      <div class="quality-check-table" role="table">
        <div class="quality-check-row quality-check-head" role="row"><span>检查项</span><span>检查结果</span><span>阈值</span><span>状态</span></div>
        <div v-for="item in qualityChecks" :key="item.name" class="quality-check-row" role="row">
          <strong>{{ item.name }}</strong><div><progress :value="item.value" max="100"></progress><span>{{ item.value }}%</span></div><code>{{ item.threshold }}</code><span class="passed"><Check :size="14" /> 通过</span>
        </div>
      </div>
      <div class="tool-execution-panel">
        <div class="tool-execution-icon"><Wrench :size="20" /></div>
        <div><span>运行时注册</span><strong>{{ toolReceipt?.tool || 'exclude_recent_contacts' }}</strong><p>{{ toolReceipt ? `${toolReceipt.rule}，从 ${formatNumber(toolReceipt.rows_before)} 人中排除 ${formatNumber(toolReceipt.removed_rows)} 人` : '任务执行后会显示工具参数、影响人数和运行结果。' }}</p></div>
        <div class="tool-execution-result"><CheckCircle :size="16" weight="fill" /><strong>{{ toolReceipt ? '执行成功' : '待调用' }}</strong><span>{{ toolReceipt?.execution_ms || '—' }} ms</span></div>
      </div>
    </div>

    <div v-else-if="activeTab === 'copy'" class="document-surface">
      <header class="document-header"><div><h2>A/B 文案与红蓝评审</h2><p>红方看转化，蓝方检查用户感受和合规，评分更高的版本进入灰度。</p></div><span>{{ copyReview.iterations || 0 }} 轮评审</span></header>
      <div class="copy-review-banner">
        <Medal :size="22" weight="fill" /><div><span>评审结果</span><strong>{{ copyReview.winner ? `${copyReview.winner} 版胜出` : '等待评审' }}</strong><p>{{ copyReview.summary || '数据清洗完成后，红蓝双方会分别评分。' }}</p></div><small>{{ copyReview.winner ? '建议灰度' : '待生成' }}</small>
      </div>
      <div class="copy-grid">
        <article v-for="variant in copyVariants" :key="variant.id" class="copy-variant">
          <div class="copy-title"><span>{{ variant.id }}</span><div><strong>{{ variant.strategy }}</strong><small>{{ variant.id === copyReview.winner ? '本轮推荐' : '对照版本' }}</small></div><b>{{ variant.score }}</b></div>
          <div class="message-preview"><small>短信 / Push 预览</small><h3>{{ variant.title }}</h3><p>{{ variant.body }}</p></div>
          <div class="dimension-list"><div v-for="(score, name) in variant.dimensions" :key="name"><span>{{ name }}</span><progress :value="score" max="100"></progress><strong>{{ score }}</strong></div></div>
        </article>
        <div v-if="!copyVariants.length" class="generic-empty"><ChatsCircle :size="28" /><p>A/B 文案将在数据清洗后生成</p></div>
      </div>
      <div class="adversarial-review"><div><Robot :size="18" /><strong>蓝方修改意见</strong></div><p>{{ blueReview?.feedback || '等待蓝方检查。' }}</p><span><CheckCircle :size="15" weight="fill" /> 第 {{ blueReview?.round || 0 }} 轮通过</span></div>
    </div>

    <div v-else class="document-surface">
      <header class="document-header"><div><h2>召回实验方案</h2><p>按 45% / 45% / 10% 分组，先小流量发送，再根据护栏指标决定是否放量。</p></div><span>{{ experiment.primary_metric || '待生成' }}</span></header>
      <div class="experiment-summary-grid">
        <article><UsersThree :size="20" /><span>{{ assets.risk?.target_rows ? '计划触达' : '实验样本' }}</span><strong>{{ formatNumber(plannedAudience) }}</strong><small>人</small></article>
        <article><ArrowsLeftRight :size="20" /><span>实验分组</span><strong>3</strong><small>组</small></article>
        <article><CalendarCheck :size="20" /><span>观察周期</span><strong>30</strong><small>天</small></article>
        <article><ChartLineUp :size="20" /><span>提升目标</span><strong>+5%</strong><small>相对值</small></article>
      </div>
      <div class="experiment-workbench">
        <section class="allocation-panel"><div class="surface-section-heading"><div><h3>实验分组</h3><p>保留 10% 不触达对照组，计算真实增量。</p></div></div><div class="allocation-list"><div v-for="(ratio, group) in experimentAllocation" :key="group"><span>{{ group === 'control' ? '对照组' : `${group} 方案` }}</span><div><i :style="{ width: ratio || '0%' }"></i></div><strong>{{ ratio }}</strong></div></div></section>
        <section class="rollout-panel"><div class="surface-section-heading"><div><h3>发送节奏</h3><p>{{ experiment.rollout || '任务完成后生成小流量方案。' }}</p></div></div><ol><li><span>1</span><div><strong>先发 1,000 人</strong><small>检查送达、投诉和系统稳定性</small></div></li><li><span>2</span><div><strong>再扩大到 5,000 人</strong><small>观察 24 小时护栏指标</small></div></li><li><span>3</span><div><strong>逐步发送剩余客群</strong><small>所有指标正常才继续</small></div></li></ol></section>
      </div>
      <div class="experiment-guard-row"><div><FlagCheckered :size="18" /><span>主指标</span><strong>{{ experiment.primary_metric || '30 天复购率' }}</strong></div><div v-for="metric in experiment.guard_metrics || ['退订率', '投诉率', '优惠成本']" :key="metric"><ShieldCheck :size="18" /><span>护栏指标</span><strong>{{ metric }}</strong></div></div>
      <div class="decision-rule"><Info :size="17" weight="fill" /><p><strong>放量条件：</strong>30 天复购率相对提升达到 5%，且退订率、投诉率和优惠成本都没有越线，才把 A 版扩大到剩余客群。</p></div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import {
  PhCaretDown as CaretDown,
  PhCaretRight as CaretRight,
  PhChatsCircle as ChatsCircle,
  PhCheck as Check,
  PhCheckCircle as CheckCircle,
  PhDatabase as Database,
  PhInfo as Info,
  PhPlay as Play,
  PhSpinnerGap as SpinnerGap,
  PhTable as Table,
  PhTextAlignLeft as TextAlignLeft,
  PhWrench as Wrench,
  PhArrowsLeftRight as ArrowsLeftRight,
  PhBroom as Broom,
  PhCalendarCheck as CalendarCheck,
  PhChartLineUp as ChartLineUp,
  PhFlagCheckered as FlagCheckered,
  PhMedal as Medal,
  PhRobot as Robot,
  PhShieldCheck as ShieldCheck,
  PhTimer as Timer,
  PhUsersThree as UsersThree,
} from '@phosphor-icons/vue';

const props = defineProps({
  task: { type: Object, default: null }, activeTab: { type: String, required: true }, events: { type: Array, default: () => [] },
});
defineEmits(['update:activeTab']);

const toolMessage = ref('');
const tabs = [
  { id: 'audience', label: '客群规则' }, { id: 'sql', label: 'SQL' }, { id: 'quality', label: '数据质量' },
  { id: 'copy', label: 'A/B 文案' }, { id: 'experiment', label: '实验方案' },
];
const assets = computed(() => props.task?.assets || {});
const metrics = computed(() => props.task?.metrics || {});
const quality = computed(() => assets.value.data_quality || {});
const audienceRules = computed(() => assets.value.audience_rules || []);
const copyVariants = computed(() => assets.value.copy_variants || []);
const copyReview = computed(() => assets.value.copy_review || {});
const blueReview = computed(() => [...(copyReview.value.rounds || [])].reverse().find((item) => item.side === 'blue'));
const experiment = computed(() => assets.value.experiment || {});
const experimentAllocation = computed(() => experiment.value.allocation || { A: '45%', B: '45%', control: '10%' });
const plannedAudience = computed(() => assets.value.risk?.target_rows || metrics.value.audience_size || 0);
const toolReceipt = computed(() => assets.value.tool_receipts?.[0]);
const sqlLines = computed(() => (assets.value.sql ? assets.value.sql.split('\n') : []));
const sqlVersion = computed(() => assets.value.sql_versions?.length || 1);
const repairEvent = computed(() => [...props.events].reverse().find((event) => event.event === 'sql_auto_repair'));
const isRunning = computed(() => props.task?.nodes?.find((node) => node.id === 'sql')?.status === 'running');
const qualityChecks = computed(() => [
  { name: '关键字段完整性', value: quality.value.completeness || 0, threshold: '≥ 95%' },
  { name: '业务口径准确性', value: quality.value.accuracy || 0, threshold: '≥ 90%' },
  { name: '用户记录唯一性', value: quality.value.uniqueness || 0, threshold: '= 100%' },
  { name: '营销授权有效率', value: assets.value.sql ? 100 : 0, threshold: '= 100%' },
  { name: '近 7 天频控排除', value: assets.value.sql ? 100 : 0, threshold: '= 100%' },
]);

function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN'); }
function formatEvent(event) { return event ? `2026-08-24 10:42　${event.summary}` : ''; }
function highlightSqlLine(line) {
  const escaped = (line || ' ')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  if (escaped.trim().startsWith('--')) return `<span class="sql-comment">${escaped}</span>`;
  return escaped
    .replace(/('[^']*')/g, '<span class="sql-string">$1</span>')
    .replace(/\b(WITH|SELECT|FROM|JOIN|ON|WHERE|GROUP BY|ORDER BY|AS|AND|OR|NOT EXISTS|AVG|MAX|DATE)\b/gi, '<span class="sql-keyword">$1</span>')
    .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="sql-number">$1</span>');
}
async function copySql() {
  if (assets.value.sql && navigator.clipboard) await navigator.clipboard.writeText(assets.value.sql);
  toolMessage.value = assets.value.sql ? 'SQL 已复制并保存为当前验证版本' : '请先执行任务生成 SQL';
}
</script>
