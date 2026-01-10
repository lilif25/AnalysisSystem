from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# 创建路由器
router = APIRouter(
    prefix="/feedback",
    tags=["反馈管理"],
    responses={404: {"description": "Not found"}},
)

# 内存存储反馈数据（实际应用中应使用数据库）
feedback_storage: Dict[str, Dict[str, Any]] = {}

class FeedbackRequest(BaseModel):
    content: str = Field(..., description="反馈内容")
    feedback_type: str = Field(..., description="反馈类型")
    user_id: str = Field(default="anonymous", description="用户ID")  # 添加默认值
    metadata: Optional[Dict[str, Any]] = None

class FeedbackResponse(BaseModel):
    id: str
    content: str
    feedback_type: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None
    status: str
    timestamp: datetime
    analysis: Optional[Dict[str, Any]] = None

@router.post("/", response_model=FeedbackResponse, summary="提交反馈")
async def create_feedback(request: FeedbackRequest):
    """
    创建新的反馈
    
    - **content**: 反馈内容
    - **feedback_type**: 反馈类型 (text, image, audio)
    - **metadata**: 可选的元数据
    
    返回创建的反馈信息
    """
    try:
        feedback_id = str(uuid.uuid4())
        
        # 创建反馈记录
        feedback = {
            "id": feedback_id,
            "content": request.content,
            "feedback_type": request.feedback_type,
            "user_id": request.user_id,
            "metadata": request.metadata or {},
            "status": "submitted",
            "timestamp": datetime.now(),
            "analysis": None
        }
        
        # 存储反馈
        feedback_storage[feedback_id] = feedback
        
        return FeedbackResponse(**feedback)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建反馈失败: {str(e)}")

@router.get("/", summary="获取反馈列表")
async def list_feedbacks(limit: int = 100, offset: int = 0):
    """
    获取反馈列表
    
    - **limit**: 返回的最大记录数
    - **offset**: 偏移量
    
    返回反馈列表和总数
    """
    try:
        # 获取所有反馈并按时间戳排序
        all_feedbacks = sorted(feedback_storage.values(), 
                              key=lambda x: x["timestamp"], 
                              reverse=True)
        
        # 应用分页
        total = len(all_feedbacks)
        feedbacks = all_feedbacks[offset:offset+limit]
        
        return {
            "feedbacks": feedbacks,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")

@router.get("/{feedback_id}", summary="获取反馈详情")
async def get_feedback(feedback_id: str):
    """
    获取特定反馈的详细信息
    
    - **feedback_id**: 反馈ID
    
    返回反馈详情
    """
    try:
        if feedback_id not in feedback_storage:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        return feedback_storage[feedback_id]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈详情失败: {str(e)}")

@router.put("/{feedback_id}", summary="更新反馈")
async def update_feedback(feedback_id: str, feedback_update: Dict[str, Any]):
    """
    更新反馈信息
    
    - **feedback_id**: 反馈ID
    - **feedback_update**: 要更新的字段
    
    返回更新后的反馈信息
    """
    try:
        if feedback_id not in feedback_storage:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        # 更新反馈
        feedback = feedback_storage[feedback_id]
        for key, value in feedback_update.items():
            if key in feedback and key != "id":  # 不允许更新ID
                feedback[key] = value
        
        feedback["timestamp"] = datetime.now()  # 更新时间戳
        
        return feedback
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新反馈失败: {str(e)}")

@router.delete("/{feedback_id}", summary="删除反馈")
async def delete_feedback(feedback_id: str):
    """
    删除反馈
    
    - **feedback_id**: 反馈ID
    
    返回删除结果
    """
    try:
        if feedback_id not in feedback_storage:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        # 删除反馈
        del feedback_storage[feedback_id]
        
        return {"message": "反馈已成功删除"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除反馈失败: {str(e)}")