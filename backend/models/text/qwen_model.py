from typing import Dict, Any, List
import sys
import os
import logging
from http import HTTPStatus
try:
    import dashscope
except ImportError:
    dashscope = None

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base_model import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QwenModel(BaseModel):
    """
    通义千问大模型接口
    """
    
    def __init__(self, api_key: str = None, model_name: str = "qwen-turbo"):
        super().__init__(None)
        self.model_name = model_name
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        
        if dashscope:
            if self.api_key:
                dashscope.api_key = self.api_key
            else:
                logger.warning("DASHSCOPE_API_KEY not found. Please set it in environment variables or pass it to constructor.")
        else:
            logger.error("dashscope library not installed.")

    def load_model(self):
        """
        Qwen API 不需要本地加载模型
        """
        pass
    
    def predict(self, input_data: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        调用 Qwen API 进行预测/对话
        """
        if not dashscope:
             return {
                "status": "error",
                "text": "dashscope library not installed."
            }

        if not dashscope.api_key:
             return {
                "status": "error",
                "text": "请配置 DASHSCOPE_API_KEY 以使用通义千问模型。"
            }

        try:
            messages = []
            if history:
                for msg in history:
                    messages.append({'role': msg['role'], 'content': msg['content']})
            
            messages.append({'role': 'user', 'content': input_data})

            response = dashscope.Generation.call(
                model=self.model_name,
                messages=messages,
                result_format='message',  # set the result to be "message" format.
            )

            if response.status_code == HTTPStatus.OK:
                return {
                    "status": "success",
                    "text": response.output.choices[0]['message']['content'],
                    "usage": response.usage
                }
            else:
                return {
                    "status": "error",
                    "code": response.code,
                    "message": response.message,
                    "text": f"Error: {response.message}"
                }
        except Exception as e:
            logger.error(f"Qwen API call failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "text": f"Exception: {str(e)}"
            }

    def preprocess(self, input_data: str) -> str:
        return input_data.strip()
        
    def postprocess(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        return output_data
