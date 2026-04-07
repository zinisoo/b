from pydantic import BaseModel, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

# 탐지 요청
class DetectionRequest(BaseModel):
    url: HttpUrl # 유효한 URL 형식인지 자동 검증
    target_name: str # 분석 대상자 이름

# 탐지 결과 응답
class DetectionResponse(BaseModel):
    task_id: str # 분석 작업 고유 ID
    status: str # processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    
# 상세 결과 조회 응답
class DetectionDetailResponse(BaseModel):
    task_id: str
    url: str  
    target_name: Optional[str] = None
    status: str
    result: Optional[Dict[str, Any]] = None
    created_at: datetime

    # 몽고디비 데이터를 Pydantic으로 변환할 때 필요한 설정
    model_config = ConfigDict(from_attributes=True)