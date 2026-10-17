"""
Syncora AI - Main FastAPI Application
Connects all services, routers, background schedulers, and database managers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_db
from services.scheduler_service import SchedulerService

# Routers
from routers.dashboard_router import router as dashboard_router
from routers.tasks_router import router as tasks_router
from routers.team_router import router as team_router
from routers.ai_router import router as ai_router
from routers.workload_router import router as workload_router
from routers.telegram_router import router as telegram_router
from routers.auth_router import router as auth_router
from routers.notifications_router import router as notifications_router
from routers.projects_router import router as projects_router
from routers.demo_router import router as demo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Seed
    init_db()
    # Start Background Task Scheduler
    await SchedulerService.start()
    yield
    # Shutdown
    await SchedulerService.stop()

app = FastAPI(
    title="Syncora AI — Group Project Coordinator Backend",
    description=(
        "Full AI Coordinator Backend integrating Telegram Bot updates, "
        "Shared Task Ledger, and the AI Invisible Workload Detector."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Frontend Development & Localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers under /api
app.include_router(dashboard_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(team_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(workload_router, prefix="/api")
app.include_router(telegram_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(demo_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name": "Syncora AI Backend",
        "status": "online",
        "docs": "/docs",
        "telegramBot": settings.TELEGRAM_BOT_NAME,
        "mode": "College Hackathon Coordinator"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "sqlite_connected",
        "telegram_service": "active",
        "workload_detector": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
