from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional

# 공통 필드
class UserBase(BaseModel):
    name: str
    email: EmailStr

# 회원가입할 때 (비밀번호 포함)
class UserCreate(UserBase):
    password: str # 프론트엔드에서 보낼 비밀번호

# 회원가입 완료 후 응답 (비밀번호 제외, ID 포함)
class UserResponse(UserBase):
    id: str = Field(alias="_id") # 몽고디비 _id를 id로 매핑

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
# 수정용 규칙
class UserUpdate(BaseModel):
    name: Optional[str] = None
    
# 로그인할 때
class UserLogin(BaseModel):
    email: EmailStr
    password: str