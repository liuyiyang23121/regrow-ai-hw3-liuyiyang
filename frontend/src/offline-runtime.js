const OFFLINE_DATE = '2026-08-24T10:42:00';
const BASE_AUDIENCE_SIZE = 12_486;
const FINAL_AUDIENCE_SIZE = 10_872;

export const isOfflineMode = window.location.protocol === 'file:' || new URLSearchParams(window.location.search).has('offline');

const SQL_V1 = `-- 高流失高客单用户：最近 30 天未下单，历史客单价 >= 500
WITH order_stats AS (
  SELECT u.user_id,
         MAX(o.paid_at) AS last_order_time,
         AVG(o.pay_amount) AS avg_order_amount
  FROM users u
  JOIN orders o ON o.user_id = u.user_id
  WHERE o.order_status = 'paid'
  GROUP BY u.user_id
)
SELECT u.user_id, u.vip_level, u.churn_score,
       os.last_order_time, os.avg_order_amount
FROM users u
JOIN order_stats os ON os.user_id = u.user_id
WHERE u.lifecycle_status = 'churn_warning'
  AND u.churn_score >= 0.70
  AND os.avg_order_amount >= 500
  AND os.last_order_time <= date('2026-08-24', '-30 day')
  AND u.marketing_consent = 1
  AND NOT EXISTS (
    SELECT 1 FROM campaign_touch_logs t
    WHERE t.user_id = u.user_id
      AND t.sent_at >= date('2026-08-24', '-7 day')
  )
ORDER BY u.churn_score DESC;`;

const SQL_V2 = SQL_V1.replace('o.pay_amount', 'o.paid_amount');

const copyVariants = [
  {
    id: 'A', strategy: '利益点前置', title: '回来看看，你的会员回归礼已准备好',
    body: '好久不见。账户内的会员回归券已可使用，适用范围与有效期以活动页为准。按需选购，我们不会频繁打扰。',
    score: 92, dimensions: { 相关性: 94, 清晰度: 92, 品牌语气: 90, 合规: 94 },
  },
  {
    id: 'B', strategy: '关系修复型', title: '我们想听听，你最近需要什么',
    body: '一段时间没见了。我们为你整理了更贴合近期偏好的商品清单；如果暂时不需要，也可以关闭此类提醒。',
    score: 88, dimensions: { 相关性: 90, 清晰度: 86, 品牌语气: 92, 合规: 91 },
  },
];

const checks = [
  { name: '敏感信息脱敏', passed: true }, { name: '黑名单过滤', passed: true },
  { name: '重复用户排重', passed: true }, { name: '时间窗口合理性', passed: true },
  { name: '人群重叠检查', passed: true },
];

const systemCatalog = {
  runtime: 'offline-demo',
  agents: [
    { name: 'Goal Planner', role: '整理目标和约束' },
    { name: 'SQL Audience Agent', role: '生成 SQL 并修复报错' },
    { name: 'Data Quality Agent', role: '清洗客群并检查质量' },
    { name: 'Strategy & Copy Agent', role: '生成 A/B 文案' },
    { name: 'Red / Blue Evaluator', role: '分别评分并给出修改意见' },
    { name: 'Guardrail', role: '检查规则并处理人工审批' },
  ],
  knowledge: [
    {
      id: 'schema', name: '数据字典', description: 'SQL Agent 可查询的表、字段和关联键',
      entries: [
        { title: 'users 用户主表', type: '表结构', summary: 'user_id、vip_level、churn_score、lifecycle_status、marketing_consent', status: '已启用' },
        { title: 'orders 支付订单表', type: '表结构', summary: 'order_id、user_id、paid_amount、paid_at、order_status', status: '已启用' },
        { title: 'campaign_touch_logs 触达日志', type: '表结构', summary: 'user_id、campaign_id、sent_at、channel，用于频控排除', status: '已启用' },
      ],
    },
    {
      id: 'metric', name: '指标口径', description: '复购率、人群门槛和统计时间范围',
      entries: [
        { title: '30 天复购率', type: '核心指标', summary: '收到触达后 30 天内再次完成支付的用户占比', status: '已启用' },
        { title: '高客单用户', type: '客群口径', summary: '近 180 天平均实付金额不低于 500 元', status: '已启用' },
        { title: '流失预警用户', type: '客群口径', summary: 'lifecycle_status = churn_warning 且 churn_score ≥ 0.70', status: '已启用' },
      ],
    },
    {
      id: 'query', name: '查询指南', description: '只读限制、字段检查和大客群查询建议',
      entries: [
        { title: '只读查询白名单', type: '安全规则', summary: '仅允许 SELECT / WITH；禁止 UPDATE、DELETE、DROP 和多语句', status: '强制' },
        { title: '字段与表校验', type: '自愈规则', summary: '执行前检查数据字典；未知字段返回可重试错误和候选字段', status: '强制' },
        { title: '查询性能优化', type: '优化指南', summary: '先过滤后关联；避免 SELECT *；大客群先灰度抽样并限制扫描范围', status: '已启用' },
      ],
    },
    {
      id: 'guardrail', name: '文案与护栏', description: '文案禁用词、7 天频控和 50,000 人审核线',
      entries: [
        { title: '营销文案禁用表达', type: '内容护栏', summary: '拦截绝对化承诺、规避关税、免税代购和过度个性化表达', status: '强制' },
        { title: '触达频控', type: '用户体验', summary: '排除最近 7 天已触达用户，并保留退订入口', status: '强制' },
        { title: '大客群人工审批', type: 'HITL', summary: '预计触达超过 50,000 人时挂起工作流，等待人工批准或驳回', status: '强制' },
      ],
    },
  ],
  tests: [
    { id: 'normal', name: '正常营销任务', description: '检查从业务目标到实验方案的六个节点能否顺序完成', scenario: 'normal', focus_tab: 'audience', expected: '生成 10,872 人客群、A/B 文案和灰度实验方案', status: 'passed' },
    { id: 'sql_repair', name: 'SQL 自动修复', description: '故意使用不存在的 pay_amount 字段，检查系统能否根据数据字典修复并重试', scenario: 'normal', focus_tab: 'sql', expected: '字段改为 paid_amount，第二次执行通过', status: 'passed' },
    { id: 'guardrail', name: '高风险护栏拦截', description: '模拟 55,000 人批量召回，检查任务暂停、人工审批和原节点恢复', scenario: 'risk', focus_tab: 'experiment', expected: '任务在安全节点暂停，批准后从该节点继续', status: 'passed' },
  ],
  verification: { automated_tests: 4, passed: 4, last_verified: '2026-08-24' },
};

const tasks = new Map();
let taskSequence = 0;

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function wait(milliseconds) { return new Promise((resolve) => window.setTimeout(resolve, milliseconds)); }

function createTask(prompt, scenario) {
  taskSequence += 1;
  const id = `OFFLINE-20260824-${String(taskSequence).padStart(3, '0')}`;
  const task = {
    id, prompt, scenario, status: 'draft', created_at: OFFLINE_DATE, updated_at: OFFLINE_DATE,
    goal: {
      objective: prompt, metric: '30 天复购率', uplift_target: '相对提升 5%',
      audience: '高流失风险、高客单价用户', observation_window: '未来 30 天',
      constraints: ['仅触达已授权用户', '排除近 7 天已触达用户', '先灰度验证，再逐步放量'],
    },
    nodes: [
      ['goal', '目标解析'], ['audience', '客群圈选'], ['sql', 'SQL 验证'],
      ['clean', '数据清洗'], ['copy', 'A/B 文案'], ['guardrail', '安全审核'],
    ].map(([nodeId, name]) => ({ id: nodeId, name, status: 'pending', summary: '等待执行', attempts: 0 })),
    assets: {},
    metrics: { audience_size: 0, data_quality: 0, sql_retries: 0, risk_level: '待评估', runtime_mode: 'offline-demo' },
    events: [], review: null,
  };
  emit(task, 'task_created', null, 'draft', '目标已整理好，确认后开始执行');
  tasks.set(id, task);
  return task;
}

function emit(task, event, node, status, summary, data = {}) {
  const item = {
    sequence: task.events.length + 1, event, task_id: task.id, node, status, summary,
    detail: null, data, timestamp: OFFLINE_DATE,
  };
  task.events.push(item);
  return item;
}

function node(task, nodeId) { return task.nodes.find((item) => item.id === nodeId); }

async function notify(callback, event) {
  if (callback) await callback(clone(event));
}

async function runNode(task, nodeId, startSummary, completeSummary, callback, applyResult) {
  const current = node(task, nodeId);
  current.status = 'running';
  current.summary = startSummary;
  await notify(callback, emit(task, 'node_started', nodeId, 'running', startSummary));
  await wait(180);
  if (applyResult) applyResult();
  current.status = 'completed';
  current.summary = completeSummary;
  await notify(callback, emit(task, 'node_completed', nodeId, 'completed', completeSummary));
}

function applyAudience(task) {
  task.assets.audience_rules = [
    { label: '流失风险', rule: 'churn_score ≥ 0.70' },
    { label: '高客单', rule: '近 180 天平均实付 ≥ 500 元' },
    { label: '近期未购', rule: '最近 30 天无支付订单' },
    { label: '触达授权', rule: 'marketing_consent = true' },
    { label: '频控排除', rule: '最近 7 天未触达' },
  ];
  task.assets.knowledge_refs = ['schema/users', 'schema/orders', 'schema/campaign_touch_logs', 'metric/30d_repurchase_rate', 'query/read_only_whitelist', 'guardrail/contact_frequency'];
}

async function runSql(task, callback) {
  const current = node(task, 'sql');
  current.status = 'running';
  current.summary = '正在生成并验证只读客群 SQL';
  await notify(callback, emit(task, 'node_started', 'sql', 'running', current.summary));
  await wait(180);
  task.assets.sql_versions = [{ version: 1, sql: SQL_V1, status: 'failed', rationale: '先生成包含可修复字段错误的 SQL v1。' }];
  current.attempts = 1;
  task.metrics.sql_retries = 1;
  await notify(callback, emit(task, 'sql_auto_repair', 'sql', 'repairing', '检测到字段 pay_amount 不存在，已自动修复为 paid_amount', { from: 'pay_amount', to: 'paid_amount' }));
  await wait(180);
  task.assets.sql_versions.push({ version: 2, sql: SQL_V2, status: 'validated', rationale: '根据数据字典把 pay_amount 修复为 paid_amount。' });
  task.assets.sql = SQL_V2;
  task.assets.sql_sample = [
    { user_id: 'U100328', vip_level: 'V4', churn_score: 0.94, last_order_time: '2026-06-18', avg_order_amount: 826 },
    { user_id: 'U102615', vip_level: 'V3', churn_score: 0.91, last_order_time: '2026-06-29', avg_order_amount: 688 },
  ];
  task.metrics.audience_size = FINAL_AUDIENCE_SIZE;
  task.metrics.sql_execution_ms = 64;
  current.attempts = 2;
  current.status = 'completed';
  current.summary = 'SQL v2 已通过，查到 10,872 名用户';
  await notify(callback, emit(task, 'node_completed', 'sql', 'completed', current.summary));
}

function applyCleaning(task) {
  task.assets.tool_registration = {
    tool: 'exclude_recent_contacts', registered_at: 'data_quality_node',
    input_schema: { base_rows: 'integer', final_rows: 'integer', days: 'integer' },
    permission: 'read_only_aggregate', status: 'registered',
  };
  task.assets.tool_receipts = [{
    tool: 'exclude_recent_contacts', status: 'success', rows_before: BASE_AUDIENCE_SIZE,
    rows_after: FINAL_AUDIENCE_SIZE, removed_rows: BASE_AUDIENCE_SIZE - FINAL_AUDIENCE_SIZE,
    rule: '最近 7 天未触达', execution_ms: 6,
  }];
  task.assets.data_quality = { score: 96, completeness: 97, accuracy: 95, uniqueness: 100, removed_rows: BASE_AUDIENCE_SIZE - FINAL_AUDIENCE_SIZE };
  task.metrics.data_quality = 96;
}

function applyCopy(task) {
  task.assets.copy_variants = clone(copyVariants);
  task.assets.copy_review = {
    iterations: 2, winner: 'A', summary: 'A 版利益点更清楚，语气不过度推销，建议先做小流量测试。',
    rounds: [
      { round: 1, side: 'red', feedback: '把会员回归礼放到前面，让用户一眼看到这条消息有什么用。', score: 89 },
      { round: 1, side: 'blue', feedback: '不要使用绝对化承诺，并写清优惠范围和有效期。', score: 88 },
      { round: 2, side: 'red', feedback: '保留开头的利益点，减少催促感。', score: 92 },
      { round: 2, side: 'blue', feedback: '适用范围和有效期已经补齐，可以先发小流量。', score: 94 },
    ],
  };
}

function applyRisk(task, requiresReview) {
  task.assets.risk = {
    level: requiresReview ? 'high' : 'low', label: requiresReview ? '高' : '低',
    requires_review: requiresReview, target_rows: requiresReview ? 55_000 : FINAL_AUDIENCE_SIZE,
    violations: [], checks: clone(checks),
  };
  task.metrics.risk_level = requiresReview ? '高' : '低';
}

function completeExperiment(task) {
  task.assets.experiment = {
    name: '高价值用户 30 天召回复购实验', allocation: { A: '45%', B: '45%', control: '10%' },
    primary_metric: '30 天复购率', guard_metrics: ['退订率', '投诉率', '优惠成本'],
    rollout: '先灰度 1,000 人，24 小时无异常后逐步放量',
  };
  task.status = 'completed';
}

async function runInitialWorkflow(task, callback, controller) {
  await runNode(task, 'goal', '正在整理目标、指标和限制条件', '目标确认：30 天复购率相对提升 5%', callback);
  if (controller.closed) return;
  await runNode(task, 'audience', '正在读取用户、订单和触达记录', '初步找到 12,486 名符合条件的用户', callback, () => applyAudience(task));
  if (controller.closed) return;
  await runSql(task, callback);
  if (controller.closed) return;
  await runNode(task, 'clean', '正在加载频控工具并排除近期已触达用户', '已排除最近 7 天触达过的 1,614 名用户', callback, () => applyCleaning(task));
  if (controller.closed) return;
  await runNode(task, 'copy', '正在生成两版文案，并交给红蓝双方评分', '两轮评审结束，A 版得分 92，建议进入小流量测试', callback, () => applyCopy(task));
  if (controller.closed) return;

  const guardrail = node(task, 'guardrail');
  guardrail.status = 'running';
  guardrail.summary = '正在检查授权、触达规模、频控和文案';
  await notify(callback, emit(task, 'node_started', 'guardrail', 'running', guardrail.summary));
  await wait(180);
  if (task.scenario === 'risk') {
    applyRisk(task, true);
    guardrail.status = 'blocked';
    guardrail.summary = '计划触达人数超过 50,000，等待人工决定';
    task.status = 'awaiting_review';
    await notify(callback, emit(task, 'review_required', 'guardrail', 'blocked', '计划触达 55,000 人，已超过 50,000 人审核线', { risk: task.assets.risk }));
    return;
  }

  applyRisk(task, false);
  guardrail.status = 'completed';
  guardrail.summary = '上线前检查通过，当前风险为低';
  await notify(callback, emit(task, 'node_completed', 'guardrail', 'completed', guardrail.summary));
  completeExperiment(task);
  await notify(callback, emit(task, 'pipeline_completed', null, 'completed', '任务完成，实验方案可以开始小流量验证'));
}

async function resumeReview(task, callback) {
  const guardrail = node(task, 'guardrail');
  const action = task.review?.action || 'reject';
  if (action === 'reject') {
    guardrail.status = 'failed';
    guardrail.summary = '人工驳回，任务已终止';
    task.status = 'rejected';
    await notify(callback, emit(task, 'review_rejected', 'guardrail', 'rejected', '人工审核已驳回，未下发任何触达任务'));
    return;
  }
  task.status = 'running';
  guardrail.status = 'running';
  await notify(callback, emit(task, 'pipeline_resumed', 'guardrail', 'running', '审核通过，任务从安全节点继续'));
  await wait(220);
  guardrail.status = 'completed';
  guardrail.summary = '审核记录已保存，可以开始小流量测试';
  await notify(callback, emit(task, 'node_completed', 'guardrail', 'completed', guardrail.summary));
  completeExperiment(task);
  await notify(callback, emit(task, 'pipeline_completed', null, 'completed', '任务完成，实验方案可以开始小流量验证'));
}

export async function offlineRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  if (path === '/api/system') return clone(systemCatalog);
  if (path === '/api/tasks' && method === 'POST') {
    const payload = JSON.parse(options.body || '{}');
    return clone(createTask(payload.prompt, payload.scenario || 'normal'));
  }

  const match = path.match(/^\/api\/tasks\/([^/]+)(?:\/(confirm|review))?$/);
  if (!match) throw new Error('离线演示不支持这个请求');
  const task = tasks.get(match[1]);
  if (!task) throw new Error('任务不存在');
  if (!match[2] && method === 'GET') return clone(task);
  if (match[2] === 'confirm' && method === 'POST') {
    task.status = 'running';
    return clone(task);
  }
  if (match[2] === 'review' && method === 'POST') {
    const payload = JSON.parse(options.body || '{}');
    task.review = { action: payload.action, comment: payload.comment || '', reviewed_at: OFFLINE_DATE, reviewer: 'PM_张宁' };
    return clone(task);
  }
  throw new Error('离线演示请求无效');
}

export function connectOfflineTask(taskId, onEvent, onError) {
  const task = tasks.get(taskId);
  const controller = { closed: false, close() { this.closed = true; } };
  if (!task) {
    if (onError) onError(new Error('任务不存在'));
    return controller;
  }
  const runner = task.status === 'awaiting_review' && task.review
    ? resumeReview(task, onEvent)
    : runInitialWorkflow(task, onEvent, controller);
  runner.catch((error) => { if (!controller.closed && onError) onError(error); });
  return controller;
}
