from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 로드

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["ttalk"]

print(db.list_collection_names())  # 연결/권한이 정상이면 [] 또는 컬렉션 목록이 출력
