# backend/app/agents/base.py
import time
from typing import AsyncGenerator, Dict, Any
# 💡 修正：重新引入标准的 Agent
from agno.agent import Agent, RunEvent 
from agno.models.openai import OpenAIChat
from app.core.config import settings
from app.core.guardrails import guardrail_manager

class FdeBaseAgent:
    """FDE 矩阵基类：统一接管 Agno 核心生命周期与流式状态切面"""
    
    def __init__(self, name: str, system_prompt: str, tools: list = None):
        self.name = name
        # 绑定高并发骨干大模型
        self.model = OpenAIChat(
            id=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        # 使用标准 Agent 进行初始化
        self.agno_agent = Agent(
            name=name,
            model=self.model,
            description=system_prompt,
            tools=tools or [],
            markdown=True,
            telemetry=False,  # 🌟 显式关闭遥测上报
        )

    async def stream_chunks(self, prompt: str) -> AsyncGenerator[str, None]:
        """统一流式切面输出，完美对接全量 CoT 观测窗"""
        try:
            # 💡 核心修改：去掉这里的 await 赋值，直接在 async for 中消费异步生成器
            async for event in self.agno_agent.arun(prompt, stream=True):
                
                # 智能兼容：提取 Agno 流事件中的文本内容
                if hasattr(event, "event") and event.event == RunEvent.run_content:
                    yield event.content
                elif hasattr(event, "content") and event.content:
                    yield event.content
                elif isinstance(event, dict):
                    yield event.get("content", "")
                elif isinstance(event, str):
                    yield event
                    
        except Exception as e:
            # 本地研发链路异常自愈提示
            yield f"\n[Stream Error in {self.name}]: {str(e)}\n"

    def run_guardrail(self, raw_data: str) -> Dict[str, Any]:
        """安全护栏切面：拦截并治理数据噪音"""
        start_time = time.time()
        cleaned_data = guardrail_manager.clean_and_validate(raw_data)
        latency = (time.time() - start_time) * 1000 
        
        return {
            "status": "PASS" if cleaned_data else "WARN",
            "latency_ms": round(latency, 2),
            "output": cleaned_data or raw_data
        }