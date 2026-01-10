from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import json
import io
import base64
import numpy as np
import sys
import os

# 添加模型路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is .../backend/api/routes
# We need to go up 2 levels to reach backend
backend_root = os.path.abspath(os.path.join(current_dir, "../.."))
models_dir = os.path.join(backend_root, "models")
text_model_dir = os.path.join(models_dir, "text")
image_model_dir = os.path.join(models_dir, "image")

sys.path.append(models_dir)
sys.path.append(text_model_dir)
sys.path.append(image_model_dir)

from text_model import TextModel
from image_model import ImageModel

# 创建路由器
router = APIRouter(
    prefix="/analyze",
    tags=["分析服务"],
    responses={404: {"description": "Not found"}},
)

# 初始化模型
text_model = TextModel()
image_model = ImageModel()

@router.post("/text", summary="文本分析")
async def analyze_text(
    text: str = Form(..., description="要分析的文本内容"),
    options: Optional[str] = Form(None, description="分析选项，JSON格式")
):
    """
    对输入的文本进行情感分析
    
    - **text**: 要分析的文本内容
    - **options**: 可选的分析参数，JSON格式
    
    返回情感分析结果，包括情感类别、置信度和关键词
    """
    try:
        # 解析选项
        analysis_options = {}
        if options:
            try:
                analysis_options = json.loads(options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="无效的JSON格式选项")
        
        # 加载模型（如果尚未加载）
        if not text_model.model:
            text_model.load_model()
        
        # 执行文本分析
        result = text_model.predict(text)
        
        # 添加元数据
        result["input_length"] = len(text)
        result["analysis_options"] = analysis_options
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本分析失败: {str(e)}")

@router.post("/image", summary="图像分析")
async def analyze_image(
    image: UploadFile = File(..., description="要分析的图像文件"),
    options: Optional[str] = Form(None, description="分析选项，JSON格式")
):
    """
    对上传的图像进行分析
    
    - **image**: 要分析的图像文件
    - **options**: 可选的分析参数，JSON格式
    
    返回图像分析结果，包括对象识别、场景理解、OCR文字提取、图像分类
    """
    try:
        # 检查文件类型
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="上传的文件不是有效的图像格式")
        
        # 解析选项
        analysis_options = {}
        if options:
            try:
                analysis_options = json.loads(options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="无效的JSON格式选项")
        
        # 读取图像数据
        image_data = await image.read()
        
        # 保存临时文件（模拟）
        temp_path = f"temp_{image.filename}"
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        # 加载模型（如果尚未加载）
        if not image_model.model:
            image_model.load_model()
        
        # 执行图像分析
        result = image_model.predict(temp_path)
        
        # 添加元数据
        result["filename"] = image.filename
        result["content_type"] = image.content_type
        result["file_size"] = len(image_data)
        result["analysis_options"] = analysis_options
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像分析失败: {str(e)}")

@router.get("/models", summary="获取可用模型信息")
async def get_models_info():
    """
    获取可用的分析模型信息
    
    返回所有可用模型的名称、版本和状态
    """
    try:
        models_info = {
            "text_model": {
                "name": text_model.model_name,
                "loaded": text_model.model is not None,
                "description": "文本分析模型"
            },
            "image_model": {
                "name": image_model.model_name,
                "loaded": image_model.model is not None,
                "description": "图像分析模型"
            }
        }
        
        return JSONResponse(content=models_info)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")
