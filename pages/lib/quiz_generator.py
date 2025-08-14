# -*- coding: utf-8 -*-
import re, json
from typing import List, Dict, Any
from lib.settings import get_openai_client

def _gpt_chat(messages, model="gpt-4o-mini", temperature=0.2, max_tokens=None) -> str:
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def compact_for_quiz_if_needed(text: str, max_chars=6000):
    text = (text or "").strip()
    if len(text) <= max_chars: return text
    sys = "아래 학습 내용을 퀴즈 생성에 필요한 핵심 개념/정의/수치/관계 위주로 800~1200자로 압축해줘."
    return _gpt_chat([{"role":"system","content":sys},{"role":"user","content":text}])

def generate_quiz(content: str, quiz_count=8) -> List[Dict[str, Any]]:
    content = compact_for_quiz_if_needed(content, max_chars=6000)
    prompt = f"""
너는 똑똑한 교육용 선생님이야. 아래의 내용을 바탕으로 다양한 유형의 퀴즈를 JSON 리스트로 만들어줘.

예시:
[
  {{
    "type": "객관식",
    "question": "예시 질문",
    "options": ["A", "B", "C", "D"],
    "answer": "A",
    "explanation": "정답 해설",
    "example": "관련 배경 설명"
  }}
]

- 반드시 'type', 'question', 'answer', 'explanation', 'example' 키 포함
- 'options'는 객관식, OX에만 포함 (주관식/빈칸형 제외)
- JSON 리스트만 출력 (설명문 금지)
- 총 {quiz_count}문제
"""
    raw = _gpt_chat([{"role":"system","content":prompt},{"role":"user","content":content}], model="gpt-4o-mini")
    raw = raw.strip()
    # 코드블록 제거
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = re.sub(r"^json", "", raw, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(raw)
        return data[:quiz_count] if isinstance(data, list) else []
    except Exception:
        return []
