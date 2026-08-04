"""
Agent 路由

接口：
    - POST /agent/run: Agent 执行接口
    - POST /agent/run/supervisor: 多 Agent 协作执行接口
"""

from fastapi import APIRouter, HTTPException, Depends
from api.schemas.agent import AgentRequest, AgentResponse
from application.service.agent_service import AgentService
from application.dependency_injection import get_agent_service
from infra.utils.log_util import logger

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/run/simple", response_model=AgentResponse)
async def agent_run(request: AgentRequest, agent_service: AgentService = Depends(get_agent_service)):
    """
    Agent 执行接口
    """
    try:
        # 记录请求日志
        logger.info(f"收到 Agent 请求, 问题: {request.question[:50]}...")

        # 执行 Agent
        result = await agent_service.run_by_simple(request.question, thread_id=request.thread_id)

        # 返回响应
        return AgentResponse(content=result)

    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run/flow", response_model=AgentResponse)
async def agent_run(request: AgentRequest, agent_service: AgentService = Depends(get_agent_service)):
    """
    Agent 执行接口
    """
    try:
        # 记录请求日志
        logger.info(f"收到 Agent 请求, 问题: {request.question[:50]}...")

        # 执行 Agent
        result = await agent_service.run_by_flow(request.question, thread_id=request.thread_id)

        # 返回响应
        return AgentResponse(content=result)

    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run/supervisor", response_model=AgentResponse)
async def agent_run_supervisor(request: AgentRequest, agent_service: AgentService = Depends(get_agent_service)):
    """
    多 Agent 协作执行接口（Supervisor 模式）

    流程：
        1. Supervisor 分析用户意图
        2. 路由到对应专家 Agent（RAG/Tool/Chat）
        3. 专家 Agent 处理问题
        4. 汇总结果并返回
    """
    try:
        logger.info(f"收到多 Agent 协作请求, 问题: {request.question[:50]}...")

        result = await agent_service.run_by_supervisor(request.question, thread_id=request.thread_id)

        return AgentResponse(content=result)

    except Exception as e:
        logger.error(f"多 Agent 协作执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))