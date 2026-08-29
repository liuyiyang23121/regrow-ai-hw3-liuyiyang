from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.tasks import router as tasks_router
from app.api.system import router as system_router
from app.core.config import settings
from app.services.agent_runtime import runtime
from app.services.database import initialise_database

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="高价值用户智能召回实验室",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(system_router)


@app.on_event("startup")
async def startup() -> None:
    initialise_database()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "runtime": runtime.mode,
        "database": str(settings.DATABASE_PATH),
    }


# 提交包直接使用已经构建好的前端，不要求接收者另装 Node.js。
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
