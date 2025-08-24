# components/api.py
import os, requests, streamlit as st

BASE = os.getenv("BACKEND_URL", "http://localhost:8080")
TIMEOUT = 10

def _headers():
    # JWT가 있다면 여기에서 Authorization 추가
    token = st.session_state.get("auth", {}).get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def _client():
    # 쿠키 세션을 쓰려면 onboarding에서 requests.Session()을 session_state에 저장 후 재사용
    return st.session_state.get("http_session") or requests

def get(path, **kwargs):
    return _client().get(f"{BASE}{path}", headers=_headers(), timeout=TIMEOUT, **kwargs)

def post(path, json=None, files=None, data=None, **kwargs):
    return _client().post(f"{BASE}{path}", json=json, files=files, data=data,
                          headers=_headers(), timeout=TIMEOUT, **kwargs)

def put(path, json=None, **kwargs):
    return _client().put(f"{BASE}{path}", json=json, headers=_headers(), timeout=TIMEOUT, **kwargs)

def delete(path, **kwargs):
    return _client().delete(f"{BASE}{path}", headers=_headers(), timeout=TIMEOUT, **kwargs)
