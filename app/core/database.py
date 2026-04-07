from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

# 다른 파일에서 불러와 쓸 수 있도록 인스턴스 생성
db_instance = MongoDB()

async def connect_to_mongo():
    # MongoDB에 연결하고 연결 상태 확인
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        
        # 실제로 연결이 잘 되었는지 확인 (Ping 테스트)
        await db_instance.client.admin.command('ping')
        print("MongoDB Atlas 연결 성공")
    except Exception as e:
        print(f"MongoDB Atlas 연결 실패: {e}")
        raise e

async def close_mongo_connection():
    # 서버 종료 시 DB 연결 닫기
    if db_instance.client:
        db_instance.client.close()
        print("MongoDB Atlas 연결 종료")