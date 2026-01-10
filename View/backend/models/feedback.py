from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FeedbackRequest(BaseModel):
    user_id: str = Field(default="anonymous", description="用户ID")
    content: str
    feedback_type: str  # text, image, audio
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class FeedbackResponse(BaseModel):
    id: str
    status: str
    message: str
    analysis: Optional[Dict[str, Any]] = None
    timestamp: datetime