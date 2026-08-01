"""
RAG 路由

接口：
    - POST /rag/query: RAG 查询
    - POST /rag/documents: 添加文档到知识库
"""

import os
import shutil
from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from api.schemas.rag import RagRequest, RagResponse
from application.service.rag_service import RAGService
from application.dependency_injection import get_rag_service
from infra.utils.log_util import logger

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=RagResponse)
async def rag_query(request: RagRequest, rag_service: RAGService = Depends(get_rag_service)):
    """
    RAG 查询接口
    
    Args:
        RagRequest: 请求模型
    
    Returns:
        RagResponse: 响应模型
    """
    try:
        logger.info(f"收到 RAG 查询请求: {request.question[:50]}...")
        
        result = await rag_service.query(
            question=request.question,
            use_rerank=False
        )
        
        return result
        
    except Exception as e:
        logger.error(f"RAG 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=str)
def rag_documents(upload_file: UploadFile = File(...), rag_service: RAGService = Depends(get_rag_service)):
    
    """
    RAG 文档接口
    
    Args:
        RagRequest: 请求模型
    
    Returns:
        RagResponse: 响应模型
    """

    logger.info(f"收到文档上传请求: {upload_file.filename}")
    try:
        temp_dir = "./temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, upload_file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
        
        rag_service.ingest_documents(file_path, incremental=True)
        os.remove(file_path)
        return f"上传成功"

        
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
        