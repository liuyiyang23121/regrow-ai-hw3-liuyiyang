# backend/app/core/guardrails.py
import time
import logging
from typing import Dict, Any, List
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] HarnessGuard - %(message)s')
logger = logging.getLogger("HarnessGuard")

# 模拟生产环境的集中式分布式 Session 状态存储器（存放 HITL 审批快照）
SESSION_CLUSTER_DB: Dict[str, Dict[str, Any]] = {}

class GuardrailManager:
    """Harness Engine 核心：全链路安全护栏与财务熔断器"""
    
    @staticmethod
    def verify_input_safety(prompt: str) -> bool:
        """输入侧护栏：防范 Prompt 注入攻击与恶意 SQL 注入危险"""
        banned_keywords = ["DROP TABLE", "DELETE FROM", "SYSTEM_PROMPT_OVERRIDE", "IGNORE PREVIOUS INSTRUCTIONS"]
        for kw in banned_keywords:
            if kw in prompt.upper():
                logger.critical(f"【🔥 触发输入护栏拦截】检测到高危非法注入攻击关键字: {kw}")
                return False
        return True

    @staticmethod
    def inspect_output_telemetry(session_id: str, agent_name: str, elapsed_time_ms: float, usage: Dict[str, int]) -> Dict[str, Any]:
        """输出侧护栏：实施 Token 财务资损防线监控与 P99 延迟上报"""
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # 资损计算：针对 gpt-oss-120b 的百万 Token 混合计价公式 (15元/M Tokens)
        financial_cost_rmb = (total_tokens / 1000000) * 15.0

        telemetry_log = {
            "agent_name": agent_name,
            "latency_ms": elapsed_time_ms,
            "total_tokens": total_tokens,
            "cost_rmb": financial_cost_rmb,
            "status": "HEALTHY"
        }

        # 1. 拦截长尾延迟 P99 告警
        if elapsed_time_ms > settings.P99_LATENCY_ALERT_MS:
            logger.error(f"【⚠️ P99 延迟警报】会话 {session_id} -> {agent_name} 耗时达 {elapsed_time_ms/1000:.2f}s，已突破灰度服务等级协议(SLA)！")
            telemetry_log["status"] = "P99_BREACH"

        # 2. 财务资损硬红线瞬间熔断
        if financial_cost_rmb > settings.COST_LIMIT_RMB or total_tokens > settings.TOKEN_BUDGET_PER_SESSION:
            logger.critical(f"【🔥 资损熔断警报】会话 {session_id} 触发极高风险算力损耗！消耗 Token: {total_tokens}，预估财务损耗: ￥{financial_cost_rmb:.4f}")
            telemetry_log["status"] = "MELTDOWN"

        return telemetry_log

guardrail_manager = GuardrailManager()