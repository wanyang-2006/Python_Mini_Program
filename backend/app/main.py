"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.quiz import router as quiz_router

app = FastAPI(
    title="AI 答题闯关 API",
    description="AI 答题闯关学习小程序后端接口",
    version="1.0.0",
)

# CORS — 开发时允许所有来源（微信开发者工具本地请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quiz_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AI答题闯关后端运行正常"}


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
