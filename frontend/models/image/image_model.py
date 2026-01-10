from typing import Dict, Any, List
import sys
import os
import random
import hashlib
import time
import logging
import requests
import base64
import json
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base_model import BaseModel

# 尝试导入 torch 和 transformers
try:
    import torch
    from transformers import pipeline
    from PIL import Image
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers or Torch not found. Falling back to simulation.")

class ImageModel(BaseModel):
    """
    图像分析模型接口 (优先使用 DashScope Qwen-VL，后备 PyTorch/Transformers)
    """
    
    def __init__(self, model_path: str = None):
        super().__init__(model_path)
        self.model_name = "image_analysis_model"
        self.pipelines = {}
        self.device = -1 # CPU by default
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-6285b3701d014538b142e05637c14b5b")
        
        # 模拟数据池 (作为后备)
        self.object_pool = ["person", "car", "dog", "cat", "tree", "building"]
        self.scene_pool = ["户外场景", "室内场景", "自然风景", "城市街景"]
        self.class_pool = ["outdoor", "indoor", "nature", "urban"]

    def load_model(self):
        """
        加载图像分析模型
        优先尝试配置 DashScope API, 否则尝试加载本地模型
        """
        # 1. 尝试使用 DashScope API
        if self.api_key:
            self.model = "DashScope API"
            logger.info("Using DashScope API (Qwen-VL) for Image Analysis.")
            return

        # 2. 尝试本地模型
        if TRANSFORMERS_AVAILABLE:
            try:
                # 检查是否有 GPU
                if torch.cuda.is_available():
                    self.device = 0
                    logger.info("Using CUDA GPU")
                elif torch.backends.mps.is_available():
                    # Mac M1/M2 support
                    self.device = "mps" 
                    logger.info("Using MPS (Apple Silicon)")
                else:
                    logger.info("Using CPU")

                logger.info("Loading Image Classification model...")
                self.pipelines['classify'] = pipeline("image-classification", model="google/vit-base-patch16-224", device=self.device)
                
                logger.info("Loading Object Detection model...")
                self.pipelines['detect'] = pipeline("object-detection", model="facebook/detr-resnet-50", device=self.device)
                
                logger.info("Loading Image Captioning model (Scene Understanding)...")
                self.pipelines['caption'] = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning", device=self.device)
                
                self.model = "Transformers Pipelines"
                logger.info("All models loaded successfully.")
                return
            except Exception as e:
                logger.error(f"Error loading real models: {e}")
                logger.info("Falling back to simulation mode.")
        
        self.model = "Simulation Mode"

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        图像分析预测
        """
        if not self.model:
            self.load_model()
        
        # 分发预测逻辑
        if self.model == "DashScope API":
            return self._predict_dashscope(image_path)
        elif self.model == "Transformers Pipelines":
            return self._predict_real(image_path)
        else:
            return self._predict_simulated(image_path)

    def _predict_dashscope(self, image_path: str) -> Dict[str, Any]:
        """使用 DashScope Qwen-VL API 进行综合分析"""
        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
                # "X-DashScope-WorkSpace": "modal" # Removed to allow default workspace access
            }
            
            # 读取并编码图像
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
            prompt = """
            请详细分析这张图片。
            请以纯JSON格式输出以下信息（不要包含markdown标记或其他文本）：
            {
                "objects": ["object1", "object2"], 
                "scene": "详细的场景描述",
                "classification": "场景分类(如:户外/室内/办公/自然)",
                "ocr_text": "图片中的所有文字内容"
            }
            对象列表只要主要物体。
            """
            
            data = {
                "model": "qwen-vl-plus",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/jpeg;base64,{encoded_string}"},
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                "parameters": {
                    "result_format": "message"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                res_data = response.json()
                try:
                    content = res_data['output']['choices'][0]['message']['content'][0]['text']
                except (KeyError, IndexError):
                     logger.error(f"Unexpected response structure: {res_data}")
                     return self._predict_simulated(image_path)

                # 清理和解析 JSON
                try:
                    # 尝试提取 ```json ... ``` 块
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                    
                    # 清理可能的非JSON字符
                    json_str = json_str.strip()
                    parsed = json.loads(json_str)
                    
                    # 格式化 objects 为前端需要的格式 {"name": str, "confidence": float}
                    objects_raw = parsed.get("objects", [])
                    objects_formatted = []
                    if isinstance(objects_raw, list):
                        for obj in objects_raw:
                            if isinstance(obj, str):
                                objects_formatted.append({"name": obj, "confidence": 0.95})
                            elif isinstance(obj, dict):
                                objects_formatted.append({"name": obj.get("name", "unknown"), "confidence": obj.get("confidence", 0.95)})
                    
                    # 格式化 classification
                    cls_raw = parsed.get("classification", "unknown")
                    classification = {}
                    if isinstance(cls_raw, str):
                        classification = {cls_raw: 0.98}
                    elif isinstance(cls_raw, dict):
                        classification = cls_raw

                    return {
                        "objects": objects_formatted,
                        "scene": parsed.get("scene", "无法描述场景"),
                        "classification": classification,
                        "ocr_text": parsed.get("ocr_text", "无文字")
                    }
                    
                except json.JSONDecodeError:
                    logger.error(f"JSON Parse Error. Content: {content}")
                    # 降级：将原始内容作为场景描述
                    return {
                        "objects": [{"name": "detected", "confidence": 0.9}],
                        "scene": content,
                        "classification": {"General": 0.9},
                        "ocr_text": "解析失败，请看场景描述"
                    }
            else:
                error_msg = f"DashScope API failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                # 如果 API 失败，尝试本地或模拟
                if TRANSFORMERS_AVAILABLE:
                    # self.load_model() # Avoid recursive reload loop issues
                    return self._predict_simulated(image_path, error_msg)
                return self._predict_simulated(image_path, error_msg)
                
        except Exception as e:
            error_msg = f"Error in DashScope prediction: {str(e)}"
            logger.error(error_msg)
            return self._predict_simulated(image_path, error_msg)

    def _predict_real(self, image_path: str) -> Dict[str, Any]:
        """使用真实模型进行预测"""
        try:
            results = {}
            
            # 1. 图像分类
            cls_res = self.pipelines['classify'](image_path)
            # 格式化分类结果: {"label": score, ...}
            classification = {item['label']: round(item['score'], 4) for item in cls_res[:3]}
            results['classification'] = classification
            
            # 2. 对象识别
            det_res = self.pipelines['detect'](image_path)
            # 格式化检测结果
            objects = []
            for item in det_res:
                objects.append({
                    "name": item['label'],
                    "confidence": round(item['score'], 4),
                    "box": [item['box']['xmin'], item['box']['ymin'], item['box']['xmax'], item['box']['ymax']]
                })
            results['objects'] = objects
            
            # 3. 场景理解 (使用 Image Captioning)
            cap_res = self.pipelines['caption'](image_path)
            if cap_res:
                results['scene'] = cap_res[0]['generated_text']
            else:
                results['scene'] = "无法描述场景"
            
            # 4. OCR (Transformers 默认没有轻量级 OCR pipeline，这里暂时模拟或留空)
            # 如果需要真实 OCR，通常需要 tesseract 或 easyocr
            results['ocr_text'] = "本地模型未启用 OCR 功能 (需安装 tesseract)"
            
            return results
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._predict_simulated(image_path, str(e))

    def _predict_simulated(self, image_path: str, error_info: str = "") -> Dict[str, Any]:
        """模拟预测 (后备方案)"""
        seed = self._get_image_hash(image_path)
        random.seed(seed)
        
        ocr_msg = "模拟OCR文本 (未加载真实模型)"
        if error_info:
            ocr_msg += f"\n\n[调试信息] API调用失败原因: {error_info}"

        return {
            "objects": self._sim_objects(),
            "scene": random.choice(self.scene_pool),
            "ocr_text": ocr_msg,
            "classification": self._sim_classification()
        }

    def preprocess(self, input_data: Any) -> Any:
        return input_data

    def postprocess(self, output_data: Any) -> Dict[str, Any]:
        return output_data
    
    def _get_image_hash(self, image_path: str) -> int:
        try:
            with open(image_path, "rb") as f:
                return int(hashlib.md5(f.read()).hexdigest(), 16)
        except:
            return int(time.time())

    def _sim_objects(self):
        return [{"name": random.choice(self.object_pool), "confidence": 0.9, "box": [0,0,100,100]}]

    def _sim_classification(self):
        return {random.choice(self.class_pool): 0.95}
