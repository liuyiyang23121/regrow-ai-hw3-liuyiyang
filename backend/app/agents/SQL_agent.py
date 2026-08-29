# backend/app/agents/SQL_agent.py
import re
from app.agents.base import FdeBaseAgent
from app.knowledge.store import EnterpriseKnowledgeStore
from app.agents.dynamic_tools import sandbox_tool_center

# 剥离出基础系统提示词，去除硬编码的静态注入
BASE_SQL_SYSTEM_PROMPT = """
你是不错的大厂高级数据治理专家（SQL Clean Agent）。
你的核心任务是：根据产品经理输入的营销描述，结合企业级数仓营销域字典架构，编写健壮、高可用的生产级 SQL 取数清洗脚本。

【硬性上线规范约束】：
1. 你的输出内容中必须包含思维链（CoT）推演，展现你是如何推导联表的。
2. 最终生成的可用 SQL 脚本必须包裹在 ```sql ... ``` 代码块内。
3. 如果你调用的 SQL 模拟运行工具返回了错误，你必须结合报错信息自动自愈重试，直到生成无缺陷代码。
"""

class SqlAgent(FdeBaseAgent):
    def __init__(self):
        # 初始化基类，系统提示词先使用标准模版
        super().__init__(
            name="SQL_Data_Clean_Agent",
            system_prompt=BASE_SQL_SYSTEM_PROMPT,
            tools=[sandbox_tool_center.mock_execute_sql_sandbox]
        )

    async def run_task(self, user_prompt: str) -> dict:
        """
        重写任务执行入口，实现动态上下文路由与安全围栏熔断拦截。
        """
        # 1. 运行时动态捕捉前端 Prompt，匹配最精准的数仓字典与安全红线
        scene_context = EnterpriseKnowledgeStore.get_context_by_scene(user_prompt)
        
        # 2. 动态拼装具备“千人千面”场景感知能力的运行时提示词
        runtime_system_prompt = f"{BASE_SQL_SYSTEM_PROMPT}\n\n当前演练场景元数据与合规红线注入：\n{scene_context}"
        self.system_prompt = runtime_system_prompt  # 动态覆盖基类提示词
        
        # 3. 调用大模型基类方法，让 LLM 结合自愈工具生成 CoT 和 SQL
        # 注意：此处根据你基类 FdeBaseAgent 的实际方法名调整（如 super().run() 或 super().execute()）
        llm_response = await super().run(user_prompt) 
        
        # 4. 从大模型返回的非结构化文本中，正则提取出生成的 SQL 脚本用于合规审计
        generated_sql = self._extract_sql(llm_response)
        
        # 5. 🔥 中间层合规拦截（Brake Agent 核心安全围栏）
        compliance_result = self._brake_agent_compliance_check(generated_sql, llm_response, scene_context)
        
        # 6. 统一组装响应格式，供下游营销 Agent 流转及前端流式渲染
        return {
            "scene_context": scene_context,
            "llm_raw_output": llm_response,
            "extracted_sql": generated_sql,
            "compliance": compliance_result
        }

    def _brake_agent_compliance_check(self, sql: str, full_text: str, scene_context: str) -> dict:
        """
        Brake Agent 核心防护网：进行语义审查与 HITL 人工审核触发判断
        """
        sql_upper = sql.upper()
        
        # 🛡️ 策略一：检查底层知识库是否声明了强制人工审核钩子（针对场景七、场景六等）
        if "trigger_hitl_brake" in scene_context or "场景七" in scene_context:
            return {
                "status": "PENDING_REVIEW",
                "action": "INTERCEPT",
                "reason": "触发场景七人工审核演练：检测到知识库明文硬编码声明，系统强制进入人工红线双通道核验流程。"
            }
            
        # 🛡️ 策略二：针对场景二的批量删改高危行为实施强拦截
        if ("UPDATE" in sql_upper or "DELETE" in sql_upper) and "USER_POINTS_REGISTRY" in sql_upper:
            # 判断是否包含危险特征
            if "WHERE" not in sql_upper or "5000000" in full_text or "全量" in full_text:
                return {
                    "status": "FORBIDDEN",
                    "action": "BLOCK",
                    "reason": "高危操作熔断：检测到针对核心资产底表 user_points_registry 的大范围写操作或无 WHERE 删改脚本，安全围栏拒绝上线！"
                }

        # 🛡️ 策略三：文案层面的合规拦截（针对场景六海关税收风险）
        if "代购" in full_text or "免税" in full_text or "规避关税" in full_text:
            return {
                "status": "PENDING_REVIEW",
                "action": "INTERCEPT",
                "reason": "策略文案触发海关跨境税收合规红线：包含‘代购/免税’违规词，流程已强行挂起，等待人工介入审计审查。"
            }

        # ✅ 策略四：绿色通道放行（针对场景一、四、五等小流量或纯只读分析）
        return {
            "status": "AUTO_PASS",
            "action": "RELEASE",
            "reason": "合规审计通过：未触发任何生产高危资产或公关合规红线，系统自动放行。验证通过按钮有效性。"
        }

    def _extract_sql(self, text: str) -> str:
        """从 markdown 文本中提取标准 sql 代码块"""
        match = re.search(r"```sql\s+(.*?)\s+```", text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""