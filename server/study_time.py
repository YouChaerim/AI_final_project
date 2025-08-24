from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, time
import pytz

from .server_db import db

router = APIRouter(prefix="/study-time", tags=["Study Time"])
KST = pytz.timezone('Asia/Seoul')

class StudyTimeData(BaseModel): hour: int; minute: int

@router.get("/{user_id}", response_model=StudyTimeData)
def get_today_study_time(user_id: str):
    try: user_obj_id = ObjectId(user_id)
    except Exception: raise HTTPException(status_code=400, detail="Invalid user ID format")
    today_kst = datetime.now(KST).date()
    start_of_day = KST.localize(datetime.combine(today_kst, time.min))
    end_of_day = KST.localize(datetime.combine(today_kst, time.max))
    pipeline = [ {"$match": { "user_id": user_obj_id, "study_date": { "$gte": start_of_day, "$lte": end_of_day } } }, { "$group": { "_id": "$user_id", "total_seconds": {"$sum": "$sum_study_time"} } } ]
    result = list(db.sessions.aggregate(pipeline))
    total_seconds = result[0].get("total_seconds", 0) if result else 0
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    return {"hour": hours, "minute": minutes}