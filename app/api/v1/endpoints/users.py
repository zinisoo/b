from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin
from app.core.database import db_instance
from app.core.security import get_password_hash
from app.core.security import verify_password
from app.core.security import create_access_token
from bson import ObjectId # 몽고디비 ID 변환용

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreate):
    # 1. 중복 이메일 체크 (이미 가입된 유저인지 확인)
    existing_user = await db_instance.db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    # 2. 비밀번호 암호화 (해시화)
    hashed_password = get_password_hash(user_in.password)

    # 3. 저장할 데이터 준비 (Pydantic 모델을 딕셔너리로 변환)
    user_data = {
        "name": user_in.name,
        "email": user_in.email,
        "hashed_password": hashed_password, # 생 비밀번호 대신 암호화된 값 저장
    }

    # 4. MongoDB에 저장
    result = await db_instance.db.users.insert_one(user_data)
    
    # 5. 저장된 데이터에 생성된 ID를 입혀서 반환
    user_data["_id"] = str(result.inserted_id)
    return user_data



@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):

    # 1. 문자열로 받은 ID를 몽고디비 전용 객체로 변환 (잘못된 형식이면 에러 발생)
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    # 2. DB에서 검색
    user = await db_instance.db.users.find_one({"_id": ObjectId(user_id)})

    # 3. 데이터가 없으면 404 에러
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 4. _id(ObjectId 객체)를 문자열로 변환
    user["_id"] = str(user["_id"])

    # 5. 조회된 데이터 반환 (Pydantic이 자동으로 id로 매핑)
    return user



@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_in: UserUpdate):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    # 1. 수정할 데이터 정리 (None이 아닌 값만 골라냄)
    update_data = {k: v for k, v in user_in.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")

    # 2. MongoDB 업데이트 명령 실행 ($set 연산자 사용)
    result = await db_instance.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    # 3. 수정된 결과 확인
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 4. 수정된 최신 데이터 다시 조회해서 반환
    updated_user = await db_instance.db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    
    return updated_user



@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    # 1. MongoDB에서 삭제 명령 실행
    result = await db_instance.db.users.delete_one({"_id": ObjectId(user_id)})

    # 2. 삭제된 데이터가 있는지 확인 (없으면 404)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="삭제할 사용자를 찾을 수 없습니다.")

    # 3. 삭제 성공 시 보통 본문 없이 204 No Content를 반환합니다.
    return None



@router.post("/login")
async def login(user_in: UserLogin):
    
    # 1. 이메일로 유저 찾기
    user = await db_instance.db.users.find_one({"email": user_in.email})
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    # 2. 비밀번호 검증 (입력값 vs DB 해시값)
    if not verify_password(user_in.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    # 3. JWT 토큰 생성
    access_token = create_access_token(data={"sub": user["email"]})
    
    # 4. 로그인 성공 응답
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(user["_id"]), 
        "name": user["name"]
    }