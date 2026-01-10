from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseModel(ABC):
    """
    所有模型的基础接口
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
    
    @abstractmethod
    def load_model(self):
        """
        加载模型
        """
        pass
    
    @abstractmethod
    def predict(self, input_data: Any) -> Dict[str, Any]:
        """
        预测方法
        """
        pass
    
    @abstractmethod
    def preprocess(self, input_data: Any) -> Any:
        """
        预处理方法
        """
        pass
    
    @abstractmethod
    def postprocess(self, output_data: Any) -> Dict[str, Any]:
        """
        后处理方法
        """
        pass