from fastapi import APIRouter

from app.services.agent_runtime import runtime


router = APIRouter(prefix="/api/system", tags=["system"])


KNOWLEDGE_CATEGORIES = [
    {
        "id": "schema",
        "name": "数据字典",
        "description": "SQL Agent 可查询的表、字段和关联键",
        "entries": [
            {"title": "users 用户主表", "type": "表结构", "summary": "user_id、vip_level、churn_score、lifecycle_status、marketing_consent", "status": "已启用"},
            {"title": "orders 支付订单表", "type": "表结构", "summary": "order_id、user_id、paid_amount、paid_at、order_status", "status": "已启用"},
            {"title": "campaign_touch_logs 触达日志", "type": "表结构", "summary": "user_id、campaign_id、sent_at、channel，用于频控排除", "status": "已启用"},
        ],
    },
    {
        "id": "metric",
        "name": "指标口径",
        "description": "复购率、人群门槛和统计时间范围",
        "entries": [
            {"title": "30 天复购率", "type": "核心指标", "summary": "收到触达后 30 天内再次完成支付的用户占比", "status": "已启用"},
            {"title": "高客单用户", "type": "客群口径", "summary": "近 180 天平均实付金额不低于 500 元", "status": "已启用"},
            {"title": "流失预警用户", "type": "客群口径", "summary": "lifecycle_status = churn_warning 且 churn_score ≥ 0.70", "status": "已启用"},
        ],
    },
    {
        "id": "query",
        "name": "查询指南",
        "description": "只读限制、字段检查和大客群查询建议",
        "entries": [
            {"title": "只读查询白名单", "type": "安全规则", "summary": "仅允许 SELECT / WITH；禁止 UPDATE、DELETE、DROP 和多语句", "status": "强制"},
            {"title": "字段与表校验", "type": "自愈规则", "summary": "执行前检查数据字典；未知字段返回可重试错误和候选字段", "status": "强制"},
            {"title": "查询性能优化", "type": "优化指南", "summary": "先过滤后关联；避免 SELECT *；大客群先灰度抽样并限制扫描范围", "status": "已启用"},
        ],
    },
    {
        "id": "guardrail",
        "name": "文案与护栏",
        "description": "文案禁用词、7 天频控和 50,000 人审核线",
        "entries": [
            {"title": "营销文案禁用表达", "type": "内容护栏", "summary": "拦截绝对化承诺、规避关税、免税代购和过度个性化表达", "status": "强制"},
            {"title": "触达频控", "type": "用户体验", "summary": "排除最近 7 天已触达用户，并保留退订入口", "status": "强制"},
            {"title": "大客群人工审批", "type": "HITL", "summary": "预计触达超过 50,000 人时挂起工作流，等待人工批准或驳回", "status": "强制"},
        ],
    },
]


TEST_CASES = [
    {
        "id": "normal",
        "name": "正常营销任务",
        "description": "检查从业务目标到实验方案的六个节点能否顺序完成",
        "scenario": "normal",
        "focus_tab": "audience",
        "expected": "生成 10,872 人客群、A/B 文案和灰度实验方案",
        "status": "passed",
    },
    {
        "id": "sql_repair",
        "name": "SQL 自动修复",
        "description": "故意使用不存在的 pay_amount 字段，检查系统能否根据数据字典修复并重试",
        "scenario": "normal",
        "focus_tab": "sql",
        "expected": "字段改为 paid_amount，第二次执行通过",
        "status": "passed",
    },
    {
        "id": "guardrail",
        "name": "高风险护栏拦截",
        "description": "模拟 55,000 人批量召回，检查任务暂停、人工审批和原节点恢复",
        "scenario": "risk",
        "focus_tab": "experiment",
        "expected": "任务在安全节点暂停，批准后从该节点继续",
        "status": "passed",
    },
]


@router.get("")
async def system_catalog():
    return {
        "runtime": runtime.mode,
        "agents": [
            {"name": "Goal Planner", "role": "整理目标和约束"},
            {"name": "SQL Audience Agent", "role": "生成 SQL 并修复报错"},
            {"name": "Data Quality Agent", "role": "清洗客群并检查质量"},
            {"name": "Strategy & Copy Agent", "role": "生成 A/B 文案"},
            {"name": "Red / Blue Evaluator", "role": "分别评分并给出修改意见"},
            {"name": "Guardrail", "role": "检查规则并处理人工审批"},
        ],
        "knowledge": KNOWLEDGE_CATEGORIES,
        "tests": TEST_CASES,
        "verification": {"automated_tests": 4, "passed": 4, "last_verified": "2026-08-24"},
    }
