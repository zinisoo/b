from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router

app = FastAPI(title="LeakCare")

# CORS 설정 추가
origins = [
    "http://localhost:5173",    # 프론트엔드 개발 서버 주소
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 허용할 도메인 목록
    allow_credentials=True,           # 쿠키 허용 여부
    allow_methods=["*"],              # 모든 HTTP 메서드(GET, POST 등) 허용
    allow_headers=["*"],              # 모든 HTTP 헤더 허용
)

# 서버 시작 시 실행
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

# 서버 종료 시 실행
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Server is running"}

app.include_router(api_router, prefix="/api/v1")