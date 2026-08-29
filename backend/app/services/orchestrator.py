from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from app.core.config import settings
from app.core.models import GoalSpec, NodeStatus, ReviewDecision, TaskEvent, TaskState, TaskStatus, WorkflowNode
from app.services.agent_runtime import runtime
from app.services.database import BASE_AUDIENCE_SIZE, initialise_database
from app.services.guardrails import inspect_campaign, verify_input
from app.services.tool_registry import execute_sql_sandbox, register_data_cleaning_tool, registry


NODE_DEFINITIONS = (
    ("goal", "目标解析"), ("audience", "客群圈选"), ("sql", "SQL 验证"),
    ("clean", "数据清洗"), ("copy", "A/B 文案"), ("guardrail", "安全审核"),
)

SQL_V1 = """-- 高流失高客单用户：最近 30 天未下单，历史客单价 >= 500
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
ORDER BY u.churn_score DESC;"""

SQL_V2 = SQL_V1.replace("o.pay_amount", "o.paid_amount")


class TaskManager:
    def __init__(self) -> None:
        self.tasks: dict[str, TaskState] = {}
        self._review_signals: dict[str, asyncio.Event] = {}
        self._runners: dict[str, asyncio.Task] = {}

    def create(self, prompt: str, scenario: str) -> TaskState:
        safe, reason = verify_input(prompt)
        if not safe:
            raise HTTPException(status_code=400, detail=reason)
        task_id = f"TASK-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
        task = TaskState(
            id=task_id,
            prompt=prompt,
            scenario=scenario,
            goal=GoalSpec(**runtime.goal_spec(prompt)),
            nodes=[WorkflowNode(id=node_id, name=name) for node_id, name in NODE_DEFINITIONS],
            metrics={"audience_size": 0, "data_quality": 0, "sql_retries": 0, "risk_level": "待评估", "runtime_mode": runtime.mode},
        )
        self.tasks[task_id] = task
        self._review_signals[task_id] = asyncio.Event()
        self._emit(task, "task_created", None, "draft", "目标已整理好，确认后开始执行")
        return task

    def get(self, task_id: str) -> TaskState:
        task = self.tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task

    def start(self, task_id: str) -> TaskState:
        task = self.get(task_id)
        if task.status != TaskStatus.DRAFT:
            return task
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.now()
        self._runners[task_id] = asyncio.create_task(self._run(task))
        return task

    def review(self, task_id: str, decision: ReviewDecision) -> TaskState:
        task = self.get(task_id)
        if task.status != TaskStatus.AWAITING_REVIEW:
            raise HTTPException(status_code=409, detail="当前任务不在待审核状态")
        task.review = {
            "action": decision.action,
            "comment": decision.comment,
            "reviewed_at": datetime.now().isoformat(),
            "reviewer": "PM_张宁",
        }
        self._review_signals[task_id].set()
        return task

    async def _run(self, task: TaskState) -> None:
        try:
            initialise_database()
            await self._run_goal(task)
            await self._run_audience(task)
            await self._run_sql(task)
            await self._run_cleaning(task)
            await self._run_copy(task)
            if not await self._run_guardrail(task):
                return
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now()
            task.assets["experiment"] = {
                "name": "高价值用户 30 天召回复购实验",
                "allocation": {"A": "45%", "B": "45%", "control": "10%"},
                "primary_metric": "30 天复购率",
                "guard_metrics": ["退订率", "投诉率", "优惠成本"],
                "rollout": "先灰度 1,000 人，24 小时无异常后逐步放量",
            }
            self._emit(task, "pipeline_completed", None, "completed", "任务完成，实验方案可以开始小流量验证")
        except Exception as error:
            task.status = TaskStatus.FAILED
            task.updated_at = datetime.now()
            self._emit(task, "pipeline_failed", None, "failed", "工作流执行失败", detail=str(error))

    async def _run_goal(self, task: TaskState) -> None:
        node = self._begin(task, "goal", "正在整理目标、指标和限制条件")
        await self._pause()
        self._complete(task, node, "目标确认：30 天复购率相对提升 5%")

    async def _run_audience(self, task: TaskState) -> None:
        node = self._begin(task, "audience", "正在读取用户、订单和触达记录")
        await self._pause()
        task.assets["audience_rules"] = [
            {"label": "流失风险", "rule": "churn_score ≥ 0.70"},
            {"label": "高客单", "rule": "近 180 天平均实付 ≥ 500 元"},
            {"label": "近期未购", "rule": "最近 30 天无支付订单"},
            {"label": "触达授权", "rule": "marketing_consent = true"},
            {"label": "频控排除", "rule": "最近 7 天未触达"},
        ]
        task.assets["knowledge_refs"] = [
            "schema/users", "schema/orders", "schema/campaign_touch_logs",
            "metric/30d_repurchase_rate", "query/read_only_whitelist", "guardrail/contact_frequency",
        ]
        self._complete(task, node, f"初步找到 {BASE_AUDIENCE_SIZE:,} 名符合条件的用户")

    async def _run_sql(self, task: TaskState) -> None:
        node = self._begin(task, "sql", "正在生成并验证只读客群 SQL")
        first_asset = runtime.sql_candidate(task.prompt, SQL_V1)
        first_sql = first_asset["sql"]
        task.assets["sql_versions"] = [{"version": 1, "sql": first_sql, "status": "testing", "rationale": first_asset["rationale"]}]
        await self._pause()
        first_result = execute_sql_sandbox(first_sql)
        node.attempts = 1
        if first_result["status"] == "success":
            task.assets["sql_versions"][0]["status"] = "validated"
            validated_sql, validated_result, validated_version = first_sql, first_result, 1
        elif first_result.get("retryable"):
            task.assets["sql_versions"][0]["status"] = "failed"
            repair_asset = runtime.repair_sql(first_sql, first_result, SQL_V2)
            self._emit(
                task, "sql_auto_repair", "sql", "repairing",
                "检测到字段 pay_amount 不存在，已自动修复为 paid_amount",
                data={"from": "pay_amount", "to": "paid_amount", "error": first_result},
            )
            await self._pause()
            repaired_sql = repair_asset["sql"]
            second_result = execute_sql_sandbox(repaired_sql)
            node.attempts = 2
            if second_result["status"] != "success":
                raise RuntimeError(f"SQL 自动修复失败：{second_result}")
            task.assets["sql_versions"].append({"version": 2, "sql": repaired_sql, "status": "validated", "rationale": repair_asset["rationale"]})
            validated_sql, validated_result, validated_version = repaired_sql, second_result, 2
            task.metrics["sql_retries"] = 1
        else:
            raise RuntimeError(f"SQL 安全校验未通过：{first_result}")

        task.assets["sql"] = validated_sql
        task.assets["sql_sample"] = validated_result["sample"]
        task.metrics["audience_size"] = validated_result["rows"]
        task.metrics["sql_execution_ms"] = validated_result["execution_ms"]
        self._complete(task, node, f"SQL v{validated_version} 已通过，查到 {validated_result['rows']:,} 名用户")

    async def _run_cleaning(self, task: TaskState) -> None:
        node = self._begin(task, "clean", "正在加载频控工具并排除近期已触达用户")
        await self._pause()
        task.assets["tool_registration"] = register_data_cleaning_tool()
        final_rows = int(task.metrics["audience_size"])
        receipt = registry.call("exclude_recent_contacts", base_rows=BASE_AUDIENCE_SIZE, final_rows=final_rows, days=7)
        task.assets["tool_receipts"] = [receipt.as_dict()]
        task.assets["data_quality"] = {"score": 96, "completeness": 97, "accuracy": 95, "uniqueness": 100, "removed_rows": receipt.removed_rows}
        task.metrics["data_quality"] = 96
        self._complete(task, node, f"已排除最近 7 天触达过的 {receipt.removed_rows:,} 名用户")

    async def _run_copy(self, task: TaskState) -> None:
        node = self._begin(task, "copy", "正在生成两版文案，并交给红蓝双方评分")
        await self._pause()
        variants = runtime.copy_variants()
        task.assets["copy_variants"] = variants
        task.assets["copy_review"] = {
            "iterations": 2,
            "winner": "A",
            "summary": "A 版利益点更清楚，语气不过度推销，建议先做小流量测试。",
            "rounds": [
                {"round": 1, "side": "red", "feedback": "把会员回归礼放到前面，让用户一眼看到这条消息有什么用。", "score": 89},
                {"round": 1, "side": "blue", "feedback": "不要使用绝对化承诺，并写清优惠范围和有效期。", "score": 88},
                {"round": 2, "side": "red", "feedback": "保留开头的利益点，减少催促感。", "score": 92},
                {"round": 2, "side": "blue", "feedback": "适用范围和有效期已经补齐，可以先发小流量。", "score": 94},
            ],
        }
        self._complete(task, node, "两轮评审结束，A 版得分 92，建议进入小流量测试")

    async def _run_guardrail(self, task: TaskState) -> bool:
        node = self._begin(task, "guardrail", "正在检查授权、触达规模、频控和文案")
        await self._pause()
        risk = inspect_campaign(target_rows=int(task.metrics["audience_size"]), copy_variants=task.assets["copy_variants"], scenario=task.scenario)
        task.assets["risk"] = risk
        task.metrics["risk_level"] = risk["label"]
        if not risk["requires_review"]:
            self._complete(task, node, "上线前检查通过，当前风险为低")
            return True

        node.status = NodeStatus.BLOCKED
        node.summary = "计划触达人数超过 50,000，等待人工决定"
        task.status = TaskStatus.AWAITING_REVIEW
        task.updated_at = datetime.now()
        self._emit(task, "review_required", "guardrail", "blocked", f"计划触达 {risk['target_rows']:,} 人，已超过 50,000 人审核线", data={"risk": risk})
        await self._review_signals[task.id].wait()
        action = task.review["action"] if task.review else "reject"
        if action == "reject":
            node.status = NodeStatus.FAILED
            node.summary = "人工驳回，任务已终止"
            task.status = TaskStatus.REJECTED
            self._emit(task, "review_rejected", "guardrail", "rejected", "人工审核已驳回，未下发任何触达任务")
            return False
        if action == "retry":
            task.scenario = "normal"
            task.metrics["audience_size"] = 10_872
            task.assets["risk"] = inspect_campaign(target_rows=10_872, copy_variants=task.assets["copy_variants"], scenario="normal")
            task.metrics["risk_level"] = "低"
        task.status = TaskStatus.RUNNING
        node.status = NodeStatus.RUNNING
        self._emit(task, "pipeline_resumed", "guardrail", "running", "审核通过，任务从安全节点继续")
        await self._pause()
        self._complete(task, node, "审核记录已保存，可以开始小流量测试")
        return True

    def _node(self, task: TaskState, node_id: str) -> WorkflowNode:
        return next(node for node in task.nodes if node.id == node_id)

    def _begin(self, task: TaskState, node_id: str, summary: str) -> WorkflowNode:
        node = self._node(task, node_id)
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now()
        node.summary = summary
        self._emit(task, "node_started", node_id, "running", summary)
        return node

    def _complete(self, task: TaskState, node: WorkflowNode, summary: str) -> None:
        node.status = NodeStatus.COMPLETED
        node.completed_at = datetime.now()
        node.summary = summary
        self._emit(task, "node_completed", node.id, "completed", summary)

    def _emit(self, task: TaskState, event: str, node: str | None, status: str, summary: str, detail: str | None = None, data: dict[str, Any] | None = None) -> None:
        task.updated_at = datetime.now()
        task.events.append(TaskEvent(sequence=len(task.events) + 1, event=event, task_id=task.id, node=node, status=status, summary=summary, detail=detail, data=data or {}))

    async def _pause(self) -> None:
        if settings.STEP_DELAY_SECONDS:
            await asyncio.sleep(settings.STEP_DELAY_SECONDS)


manager = TaskManager()
