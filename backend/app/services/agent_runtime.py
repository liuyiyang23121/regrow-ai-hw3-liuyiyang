from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings


class GoalOutput(BaseModel):
    objective: str
    metric: str
    uplift_target: str
    audience: str
    observation_window: str
    constraints: list[str] = Field(default_factory=list)


class CopyVariantOutput(BaseModel):
    id: str
    strategy: str
    title: str
    body: str
    score: int
    dimensions: dict[str, int]


class CopyBundleOutput(BaseModel):
    variants: list[CopyVariantOutput]


class SQLAssetOutput(BaseModel):
    sql: str
    rationale: str


class AgentRuntime:
    """Use an Agno model when configured; keep the homework demo deterministic otherwise."""

    def __init__(self) -> None:
        self.mode = "deterministic"
        self._model = None
        self._goal_agent = None
        self._sql_agent = None
        self._copy_agent = None
        if settings.OPENAI_API_KEY:
            try:
                from agno.agent import Agent
                from agno.models.openai import OpenAIChat
                from app.services.tool_registry import execute_sql_sandbox

                self._model = OpenAIChat(
                    id=settings.MODEL_NAME,
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                )
                self._goal_agent = Agent(
                    name="Goal Planner",
                    model=self._model,
                    output_schema=GoalOutput,
                    structured_outputs=True,
                    instructions=[
                        "把电商营销目标转换成结构化目标，不补造用户提供之外的数字。",
                        "必须给出核心指标、提升目标、目标人群、观察窗口和安全约束。",
                    ],
                )
                self._copy_agent = Agent(
                    name="Strategy & Copy Agent",
                    model=self._model,
                    output_schema=CopyBundleOutput,
                    structured_outputs=True,
                    instructions=[
                        "生成 A/B 两个差异明确的召回文案版本。",
                        "禁止绝对化承诺，必须保留适用范围、有效期或低打扰说明。",
                        "为相关性、清晰度、品牌语气和合规给出 0-100 分评分。",
                    ],
                )
                self._sql_agent = Agent(
                    name="SQL Audience Agent",
                    model=self._model,
                    tools=[execute_sql_sandbox],
                    output_schema=SQLAssetOutput,
                    structured_outputs=True,
                    instructions=[
                        "根据提供的 SQLite 数据字典生成只读客群 SQL，并调用沙盒工具验证。",
                        "只允许 SELECT 或 WITH，不得生成写操作、多语句或未知表。",
                        "users 可用字段：user_id, vip_level, churn_score, lifecycle_status, marketing_consent。",
                        "orders 可用字段：user_id, paid_amount, paid_at, order_status。",
                        "campaign_touch_logs 可用字段：user_id, sent_at, channel。",
                        "返回不带 Markdown 围栏的 SQL 和简短依据。",
                    ],
                )
                self.mode = "agno"
            except Exception:
                self._model = None

    def goal_spec(self, prompt: str) -> dict:
        if self._goal_agent is not None:
            try:
                return self._as_dict(self._goal_agent.run(prompt).content)
            except Exception:
                self.mode = "deterministic-fallback"
        return {
            "objective": prompt,
            "metric": "30 天复购率",
            "uplift_target": "相对提升 5%",
            "audience": "高流失风险、高客单价用户",
            "observation_window": "未来 30 天",
            "constraints": ["仅触达已授权用户", "排除近 7 天已触达用户", "先灰度验证，再逐步放量"],
        }

    def copy_variants(self) -> list[dict]:
        if self._copy_agent is not None:
            try:
                bundle = self._as_dict(self._copy_agent.run("为高流失、高客单且近 30 天未购买用户生成两版低打扰召回文案").content)
                if len(bundle.get("variants", [])) == 2:
                    return bundle["variants"]
            except Exception:
                self.mode = "deterministic-fallback"
        return [
            {
                "id": "A",
                "strategy": "利益点前置",
                "title": "回来看看，你的会员回归礼已准备好",
                "body": "好久不见。账户内的会员回归券已可使用，适用范围与有效期以活动页为准。按需选购，我们不会频繁打扰。",
                "score": 92,
                "dimensions": {"相关性": 94, "清晰度": 92, "品牌语气": 90, "合规": 94},
            },
            {
                "id": "B",
                "strategy": "关系修复型",
                "title": "我们想听听，你最近需要什么",
                "body": "一段时间没见了。我们为你整理了更贴合近期偏好的商品清单；如果暂时不需要，也可以关闭此类提醒。",
                "score": 88,
                "dimensions": {"相关性": 90, "清晰度": 86, "品牌语气": 92, "合规": 91},
            },
        ]

    def sql_candidate(self, prompt: str, fallback_sql: str) -> dict:
        if self._sql_agent is not None:
            try:
                result = self._as_dict(self._sql_agent.run(f"业务目标：{prompt}\n请生成并验证客群 SQL。").content)
                result["sql"] = self._clean_sql(result["sql"])
                return result
            except Exception:
                self.mode = "deterministic-fallback"
        return {"sql": fallback_sql, "rationale": "确定性演示：先生成包含可修复字段错误的 SQL v1。"}

    def repair_sql(self, sql: str, error: dict, fallback_sql: str) -> dict:
        if self._sql_agent is not None:
            try:
                result = self._as_dict(self._sql_agent.run(
                    f"上一版 SQL：\n{sql}\n\n沙盒错误：{error}\n请根据数据字典修复并重新调用沙盒验证。"
                ).content)
                result["sql"] = self._clean_sql(result["sql"])
                return result
            except Exception:
                self.mode = "deterministic-fallback"
        return {"sql": fallback_sql, "rationale": "根据 UNKNOWN_COLUMN 回执把 pay_amount 修复为 paid_amount。"}

    @staticmethod
    def _as_dict(value: Any) -> dict:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, dict):
            return value
        raise TypeError("Agent returned an unsupported structured output")

    @staticmethod
    def _clean_sql(sql: str) -> str:
        cleaned = sql.strip()
        if cleaned.startswith("```sql"):
            cleaned = cleaned[6:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()


runtime = AgentRuntime()
