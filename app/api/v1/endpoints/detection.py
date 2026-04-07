from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.schemas.metadata import MetadataCreate 
from app.schemas.detection import DetectionRequest, DetectionResponse, DetectionDetailResponse
from app.core.database import db_instance
import uuid
import asyncio
import random
from datetime import datetime

router = APIRouter()

# 가상 AI 분석 로직
async def mock_ai_analysis(url: str):

    await asyncio.sleep(5)  # 5초간 분석하는 척 대기
    
    score = random.randint(15, 98)
    items = ["email", "password", "api_key", "db_credential"]
    
    return {
        "score": score,
        "leaked_items": random.sample(items, random.randint(1, 3)),
        "is_malicious": score > 70,
        "ai_description": f"해당 사이트 분석 결과 위험도 {score}점이 감지되었습니다."
    }

async def run_analysis_and_update(task_id: str, url: str):

    try:
        # 1. 가짜 AI 분석 수행
        result_data = await mock_ai_analysis(url)
        
        # 2. DB 업데이트 (상태를 'completed'로 변경)
        await db_instance.db.detection_tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "completed",
                    "result": result_data,
                    "updated_at": datetime.now()
                }
            }
        )
        print(f"Task {task_id} 분석 완료 및 DB 업데이트 성공")
    except Exception as e:
        print(f"Task {task_id} 분석 중 오류 발생: {e}")


# 탐지 요청 엔드포인트
@router.post("/analyze", response_model=DetectionResponse, summary="Detection Request")
async def analyze_content(request_in: DetectionRequest):
    
    # 가짜 작업 ID 생성 
    task_id = str(uuid.uuid4())
    
    # 1. DB에 초기 기록 남기기 (처리 중 상태)
    new_task = {
        "task_id": task_id,
        "url": str(request_in.url),
        "target_name": request_in.target_name,
        "status": "processing",
        "result": None,
        "created_at": datetime.now()
    }
    await db_instance.db.detection_tasks.insert_one(new_task)

    # 2. 비동기로 분석 작업 시작 (사용자가 기다리지 않도록)
    asyncio.create_task(run_analysis_and_update(task_id, str(request_in.url)))
    
    return {
        "task_id": task_id,
        "status": "processing",
        "result": None
    }

# 수집 데이터 저장 요청 엔드포인트
@router.post("/metadata", status_code=status.HTTP_201_CREATED, summary="Receive Metadata")
async def receive_engine_metadata(metadata_in: MetadataCreate):

    try:
        metadata_dict = metadata_in.model_dump()
        
        # MongoDB는 Pydantic의 HttpUrl 객체를 바로 저장 못하므로 문자열 변환
        metadata_dict["target_url"] = str(metadata_dict["target_url"])
        
        # 'metadata' 컬렉션에 저장
        result = await db_instance.db.metadata.insert_one(metadata_dict)
        
        return {
            "message": "Metadata saved successfully",
            "db_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save metadata: {str(e)}"
        )
        
        
# 전체 탐지 목록 조회
@router.get("/history", response_model=List[DetectionDetailResponse], summary="Get Detection History")
async def get_detection_history():

    # 생성일(created_at) 기준 내림차순(-1) 정렬
    cursor = db_instance.db.detection_tasks.find().sort("created_at", -1)
    tasks = await cursor.to_list(length=100) # 최근 100개까지만
    
    return tasks


# 특정 작업 상세 조회 (새로고침용)
@router.get("/result/{task_id}", response_model=DetectionDetailResponse, summary="Get Specific Result")
async def get_specific_result(task_id: str):

    task = await db_instance.db.detection_tasks.find_one({"task_id": task_id})
    
    if not task:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다.")
    
    return task