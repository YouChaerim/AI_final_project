# pages/memo_folder.py
# 메모장 폴더 (메모 JSON 저장 + user_data.json 자동 저장) — 헤더 제거 + 경로 캡션 숨김 + 돌아가기 버튼(헤더 아래 우측)
import streamlit as st
import datetime as dt
import uuid
import urllib.parse
import os, json, tempfile, shutil, re, requests
from components.auth import require_login
from urllib.parse import urlencode
from components.header import render_header
from collections import defaultdict

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"
FIXED_USER_ID = "68a57b61743df4d021f534d2"

def api_list_all():
    r = requests.get(f"{BACKEND_URL}/memo-folder-api/list",
                     params={"user_id": FIXED_USER_ID}, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def api_list_by_date(date_str: str):
    r = requests.get(f"{BACKEND_URL}/memo-folder-api/list",
                     params={"user_id": FIXED_USER_ID, "date": date_str}, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def api_add(date_str: str, title: str, content: str):
    body = {"user_id": FIXED_USER_ID, "date": date_str, "title": title, "content": content}
    r = requests.post(f"{BACKEND_URL}/memo-folder-api/add", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["item"]

def api_update(memo_id: str, date_str: str, title: str, content: str):
    body = {"user_id": FIXED_USER_ID, "date": date_str, "title": title, "content": content}
    r = requests.put(f"{BACKEND_URL}/memo-folder-api/update/{memo_id}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["item"]

def api_delete(memo_id: str):
    r = requests.delete(f"{BACKEND_URL}/memo-folder-api/delete/{memo_id}",
                        params={"user_id": FIXED_USER_ID}, timeout=10)
    r.raise_for_status()
    return r.json().get("ok", False)

def _bootstrap_token_to_state_and_url():
    # 1) URL → session_state
    try:
        qp = st.query_params
    except Exception:
        qp = st.experimental_get_query_params()

    token_q = qp.get("token", None)
    if isinstance(token_q, list):
        token_q = token_q[0] if token_q else None

    # 현재 세션에 있는 값
    tok_ss = st.session_state.get("auth_token") or \
             st.session_state.get("token") or \
             st.session_state.get("access_token")

    # URL에 token이 있으면 세션에 싣기 (여러 키에 동시 저장)
    if token_q and token_q != tok_ss:
        st.session_state["auth_token"]   = token_q
        st.session_state["token"]        = token_q
        st.session_state["access_token"] = token_q
        tok_ss = token_q

    # 2) session_state → URL (URL에 없거나 다르면 추가/갱신)
    if tok_ss and token_q != tok_ss:
        # 새 API: st.query_params 할당 → rerun 유발
        st.query_params["token"] = tok_ss

    return tok_ss

# ✅ 반드시 require_login보다 먼저 호출!
_ = _bootstrap_token_to_state_and_url()


user = st.session_state.get("user", {}) or {}
USER_ID = user.get("id") or user.get("_id") or user.get("user_id") or ""

render_header()

# ===== CSS =====
st.markdown("""
<style>
header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }
section[data-testid="stSidebar"], div[data-testid="stSidebar"]{ display:none !important; }
main[data-testid="stAppViewContainer"]{ padding-left:0 !important; padding-top:0 !important; }
div[data-testid="block-container"]{ padding-top:0 !important; padding-bottom:16px !important; }

.container{ max-width:100% !important; width:100% !important;
  padding:0 clamp(16px, 3vw, 40px) 8px !important; }
.section-title{
  margin:4px 0 6px 0; padding:12px 14px; border-radius:14px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff; text-align:center; font-weight:900; font-size:30px;
  box-shadow:0 6px 14px rgba(0,0,0,.06);
}
.note-card{
  background:#fff; border-radius:14px; padding:14px 16px;
  box-shadow:0 6px 14px rgba(0,0,0,.06); margin-bottom:10px;
}
.stTextArea textarea{line-height:1.5}
.row-label{ font-size:0.92rem; font-weight:600; margin:0 0 6px 0; color:#344054; }
:root{ --search-h: 44px; --search-r: 12px; --search-pad-x: 14px; }
#search-input-anchor + div input,
#date-input-anchor + div input{ height:var(--search-h)!important; border-radius:var(--search-r)!important; padding:0 var(--search-pad-x)!important; }
#search-btn-anchor + div button{ height:var(--search-h)!important; border-radius:var(--search-r)!important; padding:0 var(--search-pad-x)!important; font-weight:800!important; width:100%!important; }
</style>
""", unsafe_allow_html=True)

# ===== 상태 초기화 =====
if "user_data" not in st.session_state:
    st.session_state.user_data = {}                     # 프리뷰에 쓰는 임시 저장소
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}                     # 각 메모별 편집 토글
if "q_committed" not in st.session_state:
    st.session_state.q_committed = ""
if "sel_date_committed" not in st.session_state:
    st.session_state.sel_date_committed = None

def _group_by_date(items):
    """/memo-folder/list 응답(items)을 날짜별로 그룹핑해 dict[date]=[...]."""
    g = defaultdict(list)
    for it in items:
        g[it["date"]].append({
            "id": it["id"],
            "date": it["date"],
            "title": it.get("title", ""),
            "content": it.get("content", ""),
            "updated": it.get("updated_at", ""),
        })
    # 날짜 역순
    return dict(sorted(g.items(), key=lambda kv: kv[0], reverse=True))

# 첫 로딩: 서버에서 전체 불러오기
if "ui_notes" not in st.session_state:
    try:
        st.session_state.ui_notes = _group_by_date(api_list_all())
    except Exception as e:
        st.session_state.ui_notes = {}
        st.warning(f"메모를 불러오지 못했어요: {e}")

notes_by_date = st.session_state.ui_notes
user_data     = st.session_state.user_data

# ===== 페이지 레이아웃 =====
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">메모장 폴더</div>', unsafe_allow_html=True)

left, right = st.columns([1, 2], gap="large")

# --- 왼쪽: 새 메모 작성 ---
with left:
    st.subheader("✍️ 새 메모")
    pick_date = st.date_input("날짜", value=dt.date.today(), format="YYYY-MM-DD")
    title = st.text_input("제목", placeholder="예) 오늘 회의 메모")
    content = st.text_area("내용", height=160, placeholder="내용을 입력하세요…")

    if st.button("추가", type="primary", use_container_width=True):
        if (title or "").strip() or (content or "").strip():
            key = pick_date.strftime("%Y-%m-%d")
            try:
                api_add(key, (title or "").strip(), (content or "").strip())
                # 새 목록 재로딩
                st.session_state.ui_notes = _group_by_date(api_list_all())
                # 프리뷰에 마지막 작성 내용 반영(선택)
                memo_text = f"{(title or '').strip()}\n{(content or '').strip()}".strip()
                st.session_state.user_data["memo"] = memo_text
                st.success("추가되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"추가 실패: {e}")
        else:
            st.warning("제목 또는 내용을 입력하세요.")

# --- 오른쪽: 날짜별 목록/검색 ---
with right:
    st.subheader("📅 날짜별 메모")

    # 날짜 범위 계산
    if notes_by_date:
        dates_sorted = sorted([dt.datetime.strptime(k, "%Y-%m-%d").date()
                               for k in notes_by_date.keys()], reverse=True)
        min_date = min(dates_sorted); max_date = max(dates_sorted)
        default_date = st.session_state.sel_date_committed or dates_sorted[0]
    else:
        dates_sorted = []
        min_date = max_date = default_date = dt.date.today()

    with st.form("memo_search", clear_on_submit=False):
        col_text, col_btn, col_date = st.columns([7, 1.2, 3])

        with col_text:
            st.markdown('<div class="row-label">제목/내용 검색</div>', unsafe_allow_html=True)
            st.markdown('<div id="search-input-anchor"></div>', unsafe_allow_html=True)
            q_input = st.text_input("검색어", placeholder="키워드를 입력하세요…",
                                    key="q_input", label_visibility="collapsed")
        with col_btn:
            st.markdown('<div class="row-label">&nbsp;</div>', unsafe_allow_html=True)
            st.markdown('<div id="search-btn-anchor"></div>', unsafe_allow_html=True)
            do_search = st.form_submit_button("검색", use_container_width=True)
        with col_date:
            st.markdown('<div class="row-label">날짜 선택</div>', unsafe_allow_html=True)
            st.markdown('<div id="date-input-anchor"></div>', unsafe_allow_html=True)
            sel_date_widget = st.date_input("",
                                            value=default_date,
                                            min_value=min_date,
                                            max_value=max_date,
                                            format="YYYY-MM-DD",
                                            key="date_input",
                                            label_visibility="collapsed")
        if do_search:
            st.session_state.q_committed = q_input
            st.session_state.sel_date_committed = sel_date_widget

    # 프리뷰 카드(‘빠른 메모’ 상태)
    st.markdown('<div class="note-card">', unsafe_allow_html=True)
    st.markdown("**현재 빠른 메모 / 오늘 할 일 (자동 반영)**")
    st.write((user_data.get("memo") or "").strip() or "—")
    todos = user_data.get("todo_items", []) or []
    if todos:
        st.markdown("**오늘 할 일**")
        for t in todos:
            st.write(f"• {t.get('text','')}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 필터링
    q = (st.session_state.q_committed or st.session_state.get("q_input", "")).lower()
    sel_date = st.session_state.sel_date_committed or st.session_state.get("date_input", default_date)
    sel_key = sel_date.strftime("%Y-%m-%d")

    day_notes = list(notes_by_date.get(sel_key, []))
    if q:
        day_notes = [n for n in day_notes
                     if q in (n.get("title","").lower()) or q in (n.get("content","").lower())]

    # 리스트 렌더링
    if day_notes:
        for n in reversed(day_notes):
            note_id = n["id"]
            st.markdown('<div class="note-card">', unsafe_allow_html=True)
            col_content, col_save, col_cancel = st.columns([4, 1, 1])

            if st.session_state.edit_mode.get(note_id, False):
                with col_content:
                    et = st.text_input("제목", value=n.get("title",""), key=f"title-{note_id}")
                    ec = st.text_area("내용", value=n.get("content",""), height=150, key=f"content-{note_id}")
                with col_save:
                    if st.button("변경 적용", key=f"save-{note_id}", type="primary", use_container_width=True):
                        try:
                            api_update(note_id, sel_key, (et or "제목 없음").strip(), ec or "")
                            st.session_state.ui_notes = _group_by_date(api_list_all())
                            st.session_state.edit_mode[note_id] = False
                            st.success("수정되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
                with col_cancel:
                    if st.button("취소", key=f"cancel-{note_id}", use_container_width=True):
                        st.session_state.edit_mode[note_id] = False
                        st.rerun()
            else:
                with col_content:
                    st.markdown(f"**{n.get('title','제목 없음')}**")
                    st.caption(f"{n.get('date','')}  ·  마지막 수정: {n.get('updated','-')}")
                    st.write(n.get("content") or " ")
                with col_save:
                    if st.button("✏️ 수정", key=f"edit-{note_id}", use_container_width=True):
                        st.session_state.edit_mode[note_id] = True
                        st.rerun()
                with col_cancel:
                    if st.button("🗑️ 삭제", key=f"del-{note_id}", use_container_width=True):
                        try:
                            api_delete(note_id)
                            st.session_state.ui_notes = _group_by_date(api_list_all())
                            st.success("삭제되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)