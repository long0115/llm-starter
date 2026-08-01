"""
Agent 路由

接口：
    - POST /agent/run: Agent 执行接口
"""

from fastapi import APIRouter, HTTPException, Depends
from api.schemas.agent import AgentRequest, AgentResponse
from application.service.agent_service import AgentService
from application.dependency_injection import get_agent_service
from infra.utils.log_util import logger

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/run", response_model=AgentResponse)
def agent_run(request: AgentRequest, agent_service: AgentService = Depends(get_agent_service)):
    """
    Agent 执行接口
    """
    try:
        # 记录请求日志
        logger.info(f"收到 Agent 请求, 问题: {request.question[:50]}...")
        
        # 执行 Agent
        result = agent_service.run_by_simple(request.question, thread_id=request.thread_id)
        
        # 返回响应
        return AgentResponse(content=result)
        
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))