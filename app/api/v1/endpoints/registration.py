from fastapi import APIRouter, File, UploadFile, HTTPException
from app.core.database import db_instance  # 어제 성공한 DB 인스턴스
from ai.register import Register           # 수진님의 AI 등록 클래스
import cv2
import numpy as np
import io
from datetime import datetime

router = APIRouter()

# 서버 시작 시 AI 모델을 미리 로드 (메모리 효율을 위해 하나만 생성)
face_register = Register()

@router.post("/face-registration")
async def register_face(file: UploadFile = File(...)):
    """
    사용자의 사진을 받아 AI 검증 후 
    정규화된 임베딩 값을 MongoDB에 저장합니다.
    """
    # 1. 파일 형식 체크
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    # 2. 업로드된 파일을 읽어서 OpenCV 이미지로 변환
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="이미지를 디코딩할 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류: {str(e)}")

    # 3. 수진님의 필살기! AI 검증 및 임베딩 추출 실행
    # (validate_for_registration -> 정규화 -> list 반환)
    result = face_register.register(image)

    # 4. 검증 실패 시 사용자에게 친절한 피드백 전달
    if not result["success"]:
        error_messages = {
            "1": "얼굴이 감지되지 않았습니다. 밝은 곳에서 다시 찍어주세요.",
            "2": "정확히 한 명의 얼굴만 있어야 합니다.",
            "3": "얼굴이 너무 작습니다. 카메라에 조금 더 가까이 와주세요.",
            "4-1": "얼굴 각도가 너무 치우쳤습니다. 정면을 응시해 주세요.",
            "4-2": "눈, 코, 입이 가려져 있습니다. 가림 없이 찍어주세요.",
            "5": "이미지 신뢰도가 낮습니다. 선명한 사진을 사용해 주세요."
        }
        step = result.get("step")
        detail_msg = error_messages.get(step, f"검증 실패 (단계: {step})")
        raise HTTPException(status_code=400, detail=detail_msg)

    # 5. 모든 검토 통과! 드디어 MongoDB에 저장
    try:
        face_data = {
            "user_email": "kim_sujin@example.com",  # 실제로는 로그인 정보에서 가져옴
            "embedding": result["embedding"],       # 512차원 정규화된 리스트
            "created_at": datetime.utcnow(),
            "filename": file.filename
        }
        
        # 'faces'라는 컬렉션에 데이터 삽입
        db_result = await db_instance.db.faces.insert_one(face_data)
        
        return {
            "status": "success",
            "message": "얼굴 등록이 성공적으로 완료되었습니다!",
            "db_id": str(db_result.inserted_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 저장 중 오류: {str(e)}")