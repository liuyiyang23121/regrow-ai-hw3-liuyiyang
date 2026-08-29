# backend/app/api/agents.py
import json
import asyncio
import random
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel  # 🔥 引入 Pydantic 依赖
from app.agents.SQL_agent import SqlAgent
from app.agents.evo_agent import EvoAgent
from app.core.guardrails import SESSION_CLUSTER_DB

router = APIRouter(prefix="/api/agents", tags=["AgentCoreGateway"])

# 初始化多智能体单例
sql_agent_instance = SqlAgent()
evo_agent_instance = EvoAgent()

# =====================================================================
# 🔥 新增：定义前端人工审核按钮的数据交互模型
# =====================================================================
class ReviewDecision(BaseModel):
    task_id: str  # 对应前端发送的 session_id 或 task_id
    action: str   # "approve" 或 "reject"


@router.get("/stream-orchestrator")
async def stream_orchestrator(
    session_id: str = Query(..., description="全局唯一会话流水号"),
    prompt: str = Query(..., description="产品经理输入的业务诉求描述")
):
    """
    基于 SSE (Server-Sent Events) 的多智能体级联编排长连接分发网关。
    """
    async def sse_event_generator():
        # 初始化分布式 Session 上下文状态
        # 🌟 【修复上下文污染】在启动每个新场景流之前，彻底重置智能体单例的旧记忆
        if hasattr(sql_agent_instance, 'memory') and sql_agent_instance.memory:
            try:
                sql_agent_instance.memory.clear()
            except Exception:
                pass
        if hasattr(evo_agent_instance, 'memory') and evo_agent_instance.memory:
            try:
                evo_agent_instance.memory.clear()
            except Exception:
                pass        


        SESSION_CLUSTER_DB[session_id] = {
            "status": "RUNNING",
            "sql_asset": None,
            "marketing_asset": None,
            "target_rows": 0,
            "hitl_approved": False,
            "raw_prompt": prompt
        }

        # 阶段一：激活 SQL 取数清洗 Agent
        sql_stream = sql_agent_instance.stream_chunks(prompt)
        async for chunk in sql_stream:
            if not chunk:
                continue
            yield f"data: {json.dumps({'type': 'cot', 'agent': 'SQL清洗智能体', 'content': chunk}, ensure_ascii=False)}\n\n"

        # 阶段二：进行风控断点判定
        # 模拟沙盒返回的规模分配：12000 正常通过，55000 触发高危熔断
        last_compiled_rows = random.choice([12000, 55000]) 
        SESSION_CLUSTER_DB[session_id]["target_rows"] = last_compiled_rows

        if last_compiled_rows > 50000:
            SESSION_CLUSTER_DB[session_id]["status"] = "SUSPENDED_AWAITING_HITL"
            
            hitl_brake_payload = {
                "event": "hitl_brake",
                "agent_name": "Harness_HITL_Manager",
                "content": f"【🚨 触发大厂风控红线拦截】当前 SQL 清洗出客群覆盖规模达 {last_compiled_rows} 人，已突破 50,000 人高客群资损资位阈值！系统已强制挂起该会话。",
                "target_rows": last_compiled_rows
            }
            yield f"data: {json.dumps(hitl_brake_payload, ensure_ascii=False)}\n\n"
            return  # 强行掐断当前流，等待人类通过独立 REST API 予以激活

        # 阶段三：级联激活红蓝对抗文案演化 Agent
        yield f"data: {json.dumps({'event': 'agent_transition', 'content': '🟢 自动化流水线流转：SQL 跑测通过且无越权风险，正式转交营销演化沙盒'}, ensure_ascii=False)}\n\n"
        
        evo_prompt = f"请针对上一步清洗出来的优质客群（规模: {last_compiled_rows} 人），结合历史金律，推演高转化文案。前置产品诉求: {prompt}"
        
        evo_stream = evo_agent_instance.stream_chunks(evo_prompt)
        async for chunk in evo_stream:
            yield f"data: {json.dumps({'type': 'cot', 'agent': '红蓝文案演化智能体', 'content': chunk}, ensure_ascii=False)}\n\n"
        
        SESSION_CLUSTER_DB[session_id]["status"] = "COMPLETED"
        yield f"data: {json.dumps({'event': 'pipeline_finished', 'content': '🎉 恭喜！全栈智能全自动模型编排与红蓝演化清洗全部闭环圆满完成。'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")


# =====================================================================
# 🔥 新增/修改：与前端 Dashboard.vue 强匹配的人工核验直接确认路由
# =====================================================================
@router.post("/review")
async def handle_human_review(decision: ReviewDecision):
    """
    接收前端人工审核按钮的点击事件，并动态解冻后端分布式状态机。
    """
    session_id = decision.task_id

    # 鲁棒性兼容：若未部署完整内存库，提供优雅的调试降级，避免死锁
    if session_id not in SESSION_CLUSTER_DB:
        # 创建临时沙盒上下文，确保点击直接成功
        SESSION_CLUSTER_DB[session_id] = {"status": "SUSPENDED_AWAITING_HITL", "hitl_approved": False}
    
    session_data = SESSION_CLUSTER_DB[session_id]
    
    # 按钮直接生效，状态就地流转
    if decision.action.lower() == "approve":
        session_data["status"] = "APPROVED_RESUME"
        session_data["hitl_approved"] = True
        return {
            "status": "SUCCESS", 
            "message": "人工审核【通过】，工作流背书解锁成功！请前端发起二次复苏通道请求。"
        }
        
    elif decision.action.lower() == "reject":
        session_data["status"] = "TERMINATED_BY_HUMAN"
        return {
            "status": "MUTED", 
            "message": "人工审核【不通过】，当前高危发布任务已被安全围栏就地熔断销毁。"
        }
        
    else:
        raise HTTPException(status_code=400, detail="非法的审核动作，仅支持 'approve' 或 'reject'")


@router.get("/resume-stream")
async def resume_stream(session_id: str = Query(..., description="解锁复苏的会话 ID")):
    """
    HITL 解锁后的二次复苏长连接。
    """
    if session_id not in SESSION_CLUSTER_DB or SESSION_CLUSTER_DB[session_id]["status"] != "APPROVED_RESUME":
        raise HTTPException(status_code=400, detail="该会话未通过安全合规复核，拒绝复苏。")

    async def resume_generator():
        yield f"data: {json.dumps({'event': 'pipeline_resume', 'content': '🚀 收到人类架构师合规解锁凭证，复苏流式管线，开始灌入红蓝对抗沙盒...'}, ensure_ascii=False)}\n\n"
        
        session_data = SESSION_CLUSTER_DB[session_id]
        evo_prompt = f"【人类特批上线】针对突发规模为 {session_data.get('target_rows', 55000)} 的高价值流失预警客群，启动最终反思演化文案。"
        
        # 动态匹配 evo_agent 内部流方法
        evo_stream = evo_agent_instance.stream_chunks(evo_prompt)
        async for chunk in evo_stream:
            yield f"data: {json.dumps({'type': 'cot', 'agent': '红蓝文案演化智能体', 'content': chunk}, ensure_ascii=False)}\n\n"
            
        session_data["status"] = "COMPLETED"
        yield f"data: {json.dumps({'event': 'pipeline_finished', 'content': '🎉 经人类特批背书的全链智能资产交付圆满结束。'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(resume_generator(), media_type="text/event-stream")