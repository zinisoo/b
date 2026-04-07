from fastapi import APIRouter
from app.api.v1.endpoints import users, detection, reports

api_router = APIRouter()

# 각 엔드포인트를 하나로 묶음
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(detection.router, prefix="/detection", tags=["detection"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])