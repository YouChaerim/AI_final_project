# server/quizzes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import ReturnDocument
import os

from .server_db import db   # ✅ 상대 import (패키지 내부)

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])  # ✅ prefix 부여
KST = timezone(timedelta(hours=9))

def _oid(x: str) -> ObjectId:
    if not ObjectId.is_valid(x):
        raise HTTPException(400, "invalid ObjectId")
    return ObjectId(x)

def _coll():
    return db[os.getenv("QUIZ_COLL", "quizzes")]  # 기본 컬렉션명: quizzes

def _users():
    return db[os.getenv("USER_COLL", "User")]  # ✅ users 컬렉션

def _get_points(uid: ObjectId) -> int:
    u = _users().find_one({"_id": uid}, {"points": 1}) or {}
    try:
        return int(u.get("points", 0))
    except Exception:
        return 0
    
def _resolve_uid_for_lookup(user_key: str) -> ObjectId:
    """
    조회용: ObjectId, local_user_id/localUserId, provider_id/providerId/provider,
    id/user_id/userId (문자/숫자 모두) 중 아무거나 받아 유저의 ObjectId로 변환
    """
    Users = _users()

    if ObjectId.is_valid(user_key):
        doc = Users.find_one({"_id": ObjectId(user_key)}, {"_id": 1})
        if doc:
            return doc["_id"]

    candidate_fields = [
        # local id 계열
        "local_user_id", "localUserId", "localId", "localid",
        # provider id 계열
        "provider_id", "providerId", "provider",
        # 기타 흔한 식별자
        "id", "user_id", "userId",
        # (옵션) 필요하면 주석 해제
        # "email", "username",
    ]

    ors = []
    for f in candidate_fields:
        ors.append({f: user_key})
        try:
            n = int(user_key)
            ors.append({f: n})
        except Exception:
            pass

    doc = Users.find_one({"$or": ors}, {"_id": 1})
    if doc:
        return doc["_id"]

    raise HTTPException(404, "user not found")

def _points_coll():
    return db[os.getenv("POINTS_COLL", "points")]

POINTS_USER_FIELD = os.getenv("POINTS_USER_FIELD", "user_id")

def _log_points(uid: ObjectId, delta: int, reason: str):
    _points_coll().insert_one({
        POINTS_USER_FIELD: uid,
        "gain_date": datetime.now(KST),
        "point": int(delta),           # +적립 / -차감
        "reason": str(reason),
    })

def _inc_points_and_log(uid: ObjectId, delta: int, reason: str):
    """User.points 증감 후 points(ledger)에 거래 기록 남김.
       delta<0면 잔액 확인까지 같이 수행."""
    cond = {"_id": uid}
    if delta < 0:
        cond["points"] = {"$gte": -delta}
    updated = _users().find_one_and_update(
        cond,
        {"$inc": {"points": int(delta)}},
        return_document=ReturnDocument.AFTER
    )
    if not updated:
        return None
    _log_points(uid, delta, reason)
    return updated

# ----- Pydantic 모델 -----
QuizType = Literal["요약", "일반", "배팅"]
QKind    = Literal["객관식","OX","단답형"]

class QuizItem(BaseModel):
    type: QKind
    quiz_text: str
    answer: Union[str, List[str]]
    choices: List[str] = []
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None

class QuizSetCreate(BaseModel):
    quiz_type: QuizType = "요약"
    quiz: List[QuizItem] = Field(default_factory=list)
    bet_point: int = 0
    reward_point: int = 0
    source: Optional[dict] = None
    summary_preview: Optional[str] = None
    content_hash: Optional[str] = None

@router.get("/points/{user_id}")
def get_points(user_id: str):
    uid = _resolve_uid_for_lookup(user_id)
    return {"points": _get_points(uid)}

@router.post("/{user_id}")
def create_quiz_set(user_id: str, payload: QuizSetCreate):
    if not payload.quiz:
        raise HTTPException(400, "quiz list is empty")
    doc = {
        "user_id": _oid(user_id),
        "quiz_type": payload.quiz_type,
        "quiz": [q.dict() for q in payload.quiz],
        "bet_point": payload.bet_point,
        "reward_point": payload.reward_point,
        "source": payload.source or {},
        "summary_preview": payload.summary_preview or "",
        "content_hash": payload.content_hash,
        "created_at": datetime.now(KST),
    }
    for q in doc["quiz"]:
        # 미답변이면 빈 문자열로
        if q.get("user_answer") is None:
            q["user_answer"] = ""
        # 오답/미답은 False (None 방지)
        if q.get("is_correct") is None:
            q["is_correct"] = False
    res = _coll().insert_one(doc)
    return {"inserted_id": str(res.inserted_id)}

@router.get("/latest/{user_id}")
def get_latest_quiz_set(user_id: str):
    doc = _coll().find_one({"user_id": _oid(user_id)}, sort=[("created_at", -1)])
    if not doc:
        raise HTTPException(404, "no quiz for user")
    doc["_id"] = str(doc["_id"]); doc["user_id"] = str(doc["user_id"])
    return doc

@router.get("/{user_id}/{quiz_id}")
def get_quiz_set(user_id: str, quiz_id: str):
    uid = _resolve_uid_for_lookup(user_id)
    doc = _coll().find_one({"_id": _oid(quiz_id), "user_id": uid})
    if not doc:
        raise HTTPException(404, "quiz not found")
    doc["_id"] = str(doc["_id"]); doc["user_id"] = str(doc["user_id"])
    return doc

class BetStart(BaseModel):
    bet_point: int = Field(..., ge=1)
    quiz: List[QuizItem]
    source: Optional[dict] = None
    summary_preview: Optional[str] = None
    content_hash: Optional[str] = None  # 동일 내용 잠금용

@router.post("/bet/start/{user_id}")
def bet_start(user_id: str, payload: BetStart):
    uid = _oid(user_id)
    if len(payload.quiz) != 10:
        raise HTTPException(400, "betting quiz must have exactly 10 items")

    # 같은 내용 반복 방지(기본 12시간)
    lock_hours = int(os.getenv("BET_LOCK_HOURS", "12"))
    if payload.content_hash:
        since = datetime.now(KST) - timedelta(hours=lock_hours)
        dup = _coll().find_one({
            "user_id": uid,
            "quiz_type": "배팅",
            "content_hash": payload.content_hash,
            "created_at": {"$gte": since}
        }, sort=[("created_at",-1)])
        if dup:
            raise HTTPException(409, "duplicate-content within lock window")

    # 포인트 선차감 (원자적)
    updated_user = _inc_points_and_log(uid, -int(payload.bet_point),
                                    f"BET_START:{int(payload.bet_point)}")
    if not updated_user:
        raise HTTPException(403, "insufficient points")
    if not updated_user:
        raise HTTPException(403, "insufficient points")

    qdocs = []
    for q in payload.quiz:
        d = q.dict()
        if d.get("user_answer") is None:
            d["user_answer"] = ""
        if d.get("is_correct") is None:
            d["is_correct"] = False
        qdocs.append(d)

    doc = {
        "user_id": uid,
        "quiz_type": "배팅",
        "quiz": qdocs,
        "bet_point": payload.bet_point,
        "reward_point": 0,
        "source": payload.source or {},
        "summary_preview": payload.summary_preview or "",
        "content_hash": payload.content_hash,
        "status": "in_progress",  # ✅ 진행 중
        "created_at": datetime.now(KST),
    }
    res = _coll().insert_one(doc)
    return {"quiz_id": str(res.inserted_id), "balance": int(updated_user.get("points", 0))}

class BetFinish(BaseModel):
    # index 순서대로 들어오는 사용자 답변(길이 10)
    answers: List[Optional[str]]

def _norm(x): return str(x).strip().lower()
def _is_corr(user_answer, answer):
    if user_answer is None:
        return False
    u = _norm(user_answer)
    if isinstance(answer, list):
        return u in {_norm(a) for a in answer}
    return u == _norm(answer)

@router.post("/bet/finish/{user_id}/{quiz_id}")
def bet_finish(user_id: str, quiz_id: str, payload: BetFinish):
    uid = _oid(user_id); qid = _oid(quiz_id)
    doc = _coll().find_one({"_id": qid, "user_id": uid, "quiz_type": "배팅"})
    if not doc:
        raise HTTPException(404, "quiz not found")
    if doc.get("status") != "in_progress":
        raise HTTPException(409, "bet already settled")

    quiz = doc.get("quiz", [])
    if len(payload.answers) != len(quiz):
        raise HTTPException(400, "answers length mismatch")

    score = 0
    for i, item in enumerate(quiz):
        ua = payload.answers[i] or ""
        corr = _is_corr(ua, item.get("answer", ""))
        item["user_answer"] = ua
        item["is_correct"] = bool(corr)
        if corr: score += 1

    # 70% 이상 성공
    need = int(round(len(quiz) * 0.7))  # 10문제면 7
    won = score >= need
    reward = int(round(doc.get("bet_point", 0) * 1.25)) if won else 0

    balance = _get_points(uid)
    if reward > 0:
        updated = _inc_points_and_log(uid, int(reward), f"BET_REWARD:{str(qid)}")
        balance = int(updated.get("points", 0))
    _coll().update_one(
        {"_id": qid, "status": "in_progress"},
        {"$set": {
            "quiz": quiz,
            "reward_point": reward,
            "bet_score": score,
            "status": "won" if won else "lost",
            "finished_at": datetime.now(KST)
        }}
    )

    # delta는 정산분만 (베팅금은 start에서 이미 차감됨)
    return {"won": won, "score": score, "delta": reward, "balance": balance,
        "bet_point": int(doc.get("bet_point", 0))}