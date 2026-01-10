from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.multimodal import router as multimodal_router
from api.routes.multimodal_analysis import router as analysis_router
# 注释掉feedback_router，避免路由冲突
# from api.routes.feedback import router as feedback_router

app = FastAPI(
    title="多模态反馈平台 API",
    description="一个支持文本、图像和音频反馈的多模态平台",
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
# 注释掉feedback_router，避免路由冲突
# app.include_router(feedback_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "欢迎使用多模态反馈平台 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)