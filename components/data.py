# components/data.py
import streamlit as st
from components.api import get, post, put

@st.cache_data(ttl=30, show_spinner=False)
def fetch_todos(user_id: str):
    r = get(f"/todos/{user_id}"); r.raise_for_status(); return r.json()

@st.cache_data(ttl=30, show_spinner=False)
def fetch_memo(user_id: str):
    r = get(f"/memos/{user_id}"); r.raise_for_status(); return r.json()

@st.cache_data(ttl=30, show_spinner=False)
def fetch_study_time(user_id: str):
    r = get(f"/study-time/{user_id}"); r.raise_for_status(); return r.json()

def toggle_todo(user_id: str, todo_id: str):
    # 백엔드 라우팅이 '/todos/toggle/{uid}/{tid}' 또는 '/todos/{uid}/toggle/{tid}' 중 무엇인지에 따라 아래 한 줄만 바꾸면 됨
    r = put(f"/todos/toggle/{user_id}/{todo_id}")
    if r.status_code == 404:
        r = put(f"/todos/{user_id}/toggle/{todo_id}")
    r.raise_for_status()
    # 상태가 바뀌었으니 캐시 무효화
    fetch_todos.clear()

def save_todos(user_id: str, items: list[dict]):
    r = post(f"/todos/{user_id}", json={"todo_items": items}); r.raise_for_status()
    fetch_todos.clear()

def save_memo(user_id: str, contents: str):
    r = post(f"/memos/{user_id}", json={"contents": contents}); r.raise_for_status()
    fetch_memo.clear()
