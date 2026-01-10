from fastapi import APIRouter
from backend.models.feedback import FeedbackRequest, FeedbackResponse
from backend.services.feedback_service import FeedbackService

router = APIRouter()
feedback_service = FeedbackService()

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    提交文本反馈
    """
    result = await feedback_service.process_feedback(request)
    return result

@router.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str):
    """
    获取特定反馈信息
    """
    result = await feedback_service.get_feedback(feedback_id)
    return result

@router.get("/feedback")
async def list_feedbacks(limit: int = 10, offset: int = 0):
    """
    获取反馈列表
    """
    result = await feedback_service.list_feedbacks(limit, offset)
    return result