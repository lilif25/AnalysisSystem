"""
Hugging Face Spaces 应用入口文件
整合FastAPI后端和Streamlit前端
"""

import os
import sys
from pathlib import Path
import subprocess
import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

# 添加项目路径到系统路径
#sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 获取当前文件所在目录（即 ～/project/View）
project_root = Path(__file__).parent.resolve()

sys.path.insert(0, str(project_root / "backend"))

# 2. 添加 models/text/（为了 text_model.py）
text_model_dir = project_root / "models" / "text"
if text_model_dir.exists():
    sys.path.insert(0, str(text_model_dir))

image_model_dir = project_root / "models" / "image"
if image_model_dir.exists():
    sys.path.insert(0, str(image_model_dir))

# 导入后端路由
from api.routes.multimodal import router as multimodal_router
from api.routes.multimodal_analysis import router as analysis_router

# 创建FastAPI应用
app = FastAPI(
    title="文本情感分析平台",
    description="一个支持文本反馈的情感分析平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(multimodal_router, prefix="/api/v1")
app.include_router(analysis_router)

# 根路径重定向到Streamlit应用
@app.get("/")
async def root():
    return RedirectResponse(url="/streamlit")

# Streamlit应用路径
@app.get("/streamlit")
async def streamlit_app():
    return """
    <html>
        <head>
            <title>多模态分析平台</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    text-align: center;
                    background-color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #333;
                }
                p {
                    color: #666;
                    margin-bottom: 2rem;
                }
                a {
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }
                a:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>多模态分析平台</h1>
                <p>这是一个支持文本、图像和音频反馈的多模态分析平台</p>
                <a href="/api/v1/docs" target="_blank">查看API文档</a>
            </div>
        </body>
    </html>
    """

# 启动Streamlit应用的线程函数
def run_streamlit():
    """在后台启动Streamlit应用"""
    time.sleep(3)  # 等待FastAPI启动
    os.chdir(os.path.join(os.path.dirname(__file__), 'frontend'))
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "multimodal_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false"
    ])

# 在后台线程中启动Streamlit
streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
streamlit_thread.start()

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multimodal-platform"}

if __name__ == "__main__":
    # 启动FastAPI应用
    uvicorn.run(app, host="0.0.0.0", port=7860)
