# pages/wrong_folder.py
import streamlit as st
import datetime as dt
import uuid
import json, os, tempfile, shutil, requests
from components.header import render_header
from components.auth import require_login
from urllib.parse import urlencode
from collections import defaultdict

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"  # 파일에 이미 있다면 그 값 사용
FIXED_USER_ID = "68a57b61743df4d021f534d2"

# -------------------- API helpers --------------------
def api_wrong_list(date_str: str | None = None):
    params = {"user_id": FIXED_USER_ID}
    if date_str:
        params["date"] = date_str
    r = requests.get(f"{BACKEND_URL}/wrong-folder-api/list", params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def api_wrong_add(date_str: str, question: str, my_answer: str, correct_answer: str,
                  explanation: str, image: str | None = None, source: str | None = None,
                  page: int | None = None):
    body = {
        "user_id": FIXED_USER_ID, "date": date_str,
        "question": question, "my_answer": my_answer, "correct_answer": correct_answer,
        "explanation": explanation, "image": image, "source": source, "page": page
    }
    r = requests.post(f"{BACKEND_URL}/wrong-folder-api/add", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["item"]

def api_wrong_update(item_id: str, date_str: str, question: str, my_answer: str,
                     correct_answer: str, explanation: str, image: str | None,
                     source: str | None, page: int | None):
    body = {
        "user_id": FIXED_USER_ID, "date": date_str,
        "question": question, "my_answer": my_answer, "correct_answer": correct_answer,
        "explanation": explanation, "image": image, "source": source, "page": page
    }
    r = requests.put(f"{BACKEND_URL}/wrong-folder-api/update/{item_id}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["item"]

def api_wrong_delete(item_id: str):
    r = requests.delete(
        f"{BACKEND_URL}/wrong-folder-api/delete/{item_id}",
        params={"user_id": FIXED_USER_ID}, timeout=10
    )
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


# ========================= 상단바 제거 & 스타일 =========================
st.markdown("""
<style>
/* 0) 페이지/루트 여백 완전 제거 */
html, body { margin:0 !important; padding:0 !important; }
main.stApp{ padding-top:0 !important; }

/* 0.5) 사이드바 완전 숨김 + 좌측 여백 제거 */
section[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebarContent"]{ display:none !important; }
[data-testid="stAppViewContainer"]{ padding-left:0 !important; }

/* 1) Streamlit 기본 UI 숨김 */
header[data-testid="stHeader"]{ display:none !Important; }
div[data-testid="stToolbar"]{ display:none !important; }
div[data-testid="stDecoration"]{ display:none !important; }
div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }

/* 1-1) 제목 옆 링크(체인) 아이콘 숨기기 */
h1 > a, h2 > a, h3 > a, h4 > a, h5 > a, h6 > a { display:none !important; }

/* 2) 컨테이너 상단 패딩 0 */
[data-testid="stAppViewContainer"]{ padding-top:0 !important; }
div[data-testid="block-container"],
div[class*="block-container"]{ padding-top:0 !important; padding-bottom:12px !important; }

/* 3) 첫 요소 margin-top 0 */
div[data-testid="block-container"] > div:first-child{ margin-top:0 !important; padding-top:0 !important; }
h1,h2,h3,h4,h5,h6{ margin-top:0 !important; }

[data-testid="stAppViewContainer"] > .main .block-container{
  max-width:100% !important;
  width:100% !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

            
div[data-testid="block-container"]{
  max-width:100% !important;
  width:100% !important;
  margin-left:0 !important;
  margin-right:0 !important;
  padding-left:0 !important;
  padding-right:0 !important;
}

/* 우리가 쓰는 컨테이너도 와이드 + 반응형 패딩 */
.container{
  max-width:100% !important;
  width:100% !important;
  padding:0 clamp(16px, 3vw, 40px) 8px !important;
}

/* 메인헤더(오렌지 그라데이션 바) */
.panel-head{
  margin-top:0;
  border-radius:18px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff;
  font-size:28px; font-weight:900; text-align:center;
  padding:16px 20px;
  box-shadow:0 8px 18px rgba(0,0,0,.06);
}

/* 통계칩 / 툴바 */
.statbar{display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 8px 0;}
.statchip{
  background:#FFFFFF; border-radius:12px; padding:8px 10px;
  box-shadow:0 2px 10px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06);
  font-weight:800; font-size:14px;
}
.toolbar{display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin:0 0 6px 0;}
label{ font-size:0.92rem !important; margin-bottom:4px !important; }

/* 칩 */
.pill{display:inline-block; padding:6px 10px; border-radius:999px; background:#F6F7F9; font-size:12px; color:#555; margin-right:6px;}
.pill.src{background:#eef3ff; color:#1b3c8c;}

/* ===== 카드 / 답변 박스 ===== */
.card{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 0 10px 0 !important;
}
.card-title{font-weight:800; font-size:16px; margin:0 0 6px;}
.answer-row{display:flex; gap:12px; align-items:flex-start; flex-wrap:wrap}
.answer-box{ flex:1 1 280px; border-radius:12px; padding:10px 12px; border:1px solid #eee; background:#fafafa; }
.answer-good{ border-color:#d4f5d4; background:#f6fff6; }
.answer-bad{  border-color:#ffd6d6; background:#fff6f6; }

/* 이미지 */
img.qimg{border-radius:12px; border:1px solid rgba(0,0,0,.06); max-height:240px; object-fit:contain}

/* 저장폴더 이동 버튼 스타일 */
#go-folder-left + div button{
  background:#fff !important;
  color:#111 !important;
  border:1px solid rgba(0,0,0,.12) !important;
  padding:4px 10px !important;
  font-size:14px !important;
  border-radius:10px !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
}
#go-folder-left + div button:hover{ border-color:rgba(0,0,0,.2) !important; }

/* Expander(오답 추가) 흰색 박스/그림자/테두리 제거 */
div[data-testid="stExpander"]{ background:transparent !important; border:0 !important; box-shadow:none !important; }
div[data-testid="stExpander"] > details{ background:transparent !important; border:0 !important; box-shadow:none !important; }
div[data-testid="stExpander"] div[role="button"]{ background:transparent !important; border:0 !important; box-shadow:none !important; padding-left:0 !important; padding-right:0 !important; }
div[data-testid="stExpander"] div[role="button"] p{ margin:0 !important; }

/* 보험: 알림/배너 다음 빈 블록 숨김 */
div[role="alert"] + div:empty,
div[data-testid="stAlert"] + div:empty,
div[role="alert"] + div[data-testid="stVerticalBlock"]:empty,
div[data-testid="stVerticalBlock"]:empty { display:none !important; }

/* 통일 라벨(수동 출력) */
.row-label{
  font-size:0.92rem;
  font-weight:600;
  margin:0 0 6px 0;
  color:#344054;
}
</style>
""", unsafe_allow_html=True)

# -------------------- 상태 --------------------
if "wb_items" not in st.session_state:
    try:
        st.session_state.wb_items = api_wrong_list()   # 전체 날짜 로드
    except Exception as e:
        st.session_state.wb_items = []
        st.error(f"오답을 불러오지 못했어요: {e}")

if "wb_edit" not in st.session_state:
    st.session_state.wb_edit = {}      # {item_id: bool}
if "q_committed" not in st.session_state:
    st.session_state.q_committed = ""
if "sel_date_committed" not in st.session_state:
    st.session_state.sel_date_committed = None

def _group_by_date(items):
    g = defaultdict(list)
    for it in items:
        # 서버가 date 필드를 주면 사용, 없으면 created_at의 YYYY-MM-DD 사용
        date_key = it.get("date") or (it.get("created_at","")[:10] if it.get("created_at") else "")
        it["date"] = date_key
        g[date_key].append(it)
    return dict(sorted(g.items(), key=lambda kv: kv[0], reverse=True))

wb_by_date = _group_by_date(st.session_state.wb_items)

# -------------------- 헤더 --------------------
st.markdown("""
<div class="container">
  <div class="panel-head">오답 폴더</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='container'>", unsafe_allow_html=True)

# -------------------- 통계칩 --------------------
today_str = dt.date.today().strftime("%Y-%m-%d")
this_week = dt.date.today().isocalendar().week
all_items = list(st.session_state.wb_items)
cnt_total = len(all_items)
cnt_today = sum(1 for it in all_items if (it.get("date") or "") == today_str)
cnt_week  = 0
for it in all_items:
    d = it.get("date")
    if not d:
        continue
    y, m, d2 = map(int, d.split("-"))
    if dt.date(y, m, d2).isocalendar().week == this_week:
        cnt_week += 1

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="statchip">총 오답: {cnt_total}</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="statchip">오늘: {cnt_today}</div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="statchip">이번 주: {cnt_week}</div>', unsafe_allow_html=True)

# -------------------- 검색/날짜 선택 --------------------
with st.form("searchbar", clear_on_submit=False):
    col_search, col_date = st.columns([7, 3])
    with col_search:
        st.markdown('<div class="row-label">제목/내용 검색</div>', unsafe_allow_html=True)
        s1, s2 = st.columns([10, 2])
        with s1:
            q_input = st.text_input("검색어", placeholder="키워드…",
                                    key="q_input", label_visibility="collapsed")
        with s2:
            do_search = st.form_submit_button("검색", use_container_width=True)
    with col_date:
        st.markdown('<div class="row-label">날짜 선택</div>', unsafe_allow_html=True)
        # 날짜 목록이 없으면 오늘로
        all_dates = sorted([k for k in wb_by_date.keys() if k], reverse=True)
        default_date = (st.session_state.sel_date_committed or
                        (dt.datetime.strptime(all_dates[0], "%Y-%m-%d").date() if all_dates else dt.date.today()))
        sel_date_widget = st.date_input("",
                                        value=default_date,
                                        format="YYYY-MM-DD",
                                        key="date_input",
                                        label_visibility="collapsed")
    if do_search:
        st.session_state.q_committed = q_input
        st.session_state.sel_date_committed = sel_date_widget

st.divider()

# -------------------- 필터/정렬 --------------------
q = (st.session_state.get("q_committed") or st.session_state.get("q_input", "")).lower()
sel_date = st.session_state.get("sel_date_committed") or st.session_state.get("date_input", dt.date.today())
sel_key = sel_date.strftime("%Y-%m-%d")

day_items = list(wb_by_date.get(sel_key, []))
if q:
    def _blob(it):
        return " ".join([
            it.get("question",""), it.get("my_answer",""), it.get("correct_answer",""),
            it.get("explanation",""), it.get("source","")
        ]).lower()
    day_items = [it for it in day_items if q in _blob(it)]

# 오답 먼저, 그다음 수정시각 오름차순
day_items.sort(key=lambda it: ((it.get("my_answer") == it.get("correct_answer")), it.get("updated_at","")))

# -------------------- 렌더/조작 --------------------
def _reload_all():
    st.session_state.wb_items = api_wrong_list()
    st.rerun()

def banner_success(msg: str):
    st.markdown(
        f"<div style='background:#EAF7EE;border:1px solid #D6F0DD;"
        f"color:#1C7C3A;border-radius:8px;padding:12px 14px;font-weight:700;'>{msg}</div>",
        unsafe_allow_html=True
    )

def banner_info(msg: str):
    st.markdown(
        f"<div style='background:#F6F7F9;border:1px solid #E5E7EB;"
        f"color:#344054;border-radius:8px;padding:12px 14px;font-weight:600;'>{msg}</div>",
        unsafe_allow_html=True
    )

if not day_items:
    banner_info("이 날짜에는 오답이 없습니다. 아래에서 새 오답을 추가해 보세요.")
else:
    for it in day_items:
        iid = it["id"]
        is_edit = st.session_state.wb_edit.get(iid, False)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        if is_edit:
            et_q   = st.text_area("문제", value=it.get("question",""), key=f"q-{iid}")
            c1, c2 = st.columns(2)
            with c1:
                et_my   = st.text_input("내 답", value=it.get("my_answer",""), key=f"my-{iid}")
                et_src  = st.text_input("출처(예: OCR/교재명)", value=it.get("source",""), key=f"src-{iid}")
            with c2:
                et_cor  = st.text_input("정답", value=it.get("correct_answer",""), key=f"cor-{iid}")
                et_page = st.number_input("페이지(옵션)", min_value=0,
                                          value=int(it.get("page") or 0), key=f"page-{iid}")
            et_exp  = st.text_area("피드백(해설)", value=it.get("explanation",""), key=f"exp-{iid}")
            et_img  = st.text_input("이미지 URL(옵션)", value=it.get("image") or "", key=f"img-{iid}")

            b1, b2 = st.columns(2)
            with b1:
                if st.button("저장", key=f"save-{iid}", type="primary", use_container_width=True):
                    try:
                        api_wrong_update(
                            iid, it.get("date") or sel_key,
                            (et_q or "").strip(), (et_my or "").strip(),
                            (et_cor or "").strip(), (et_exp or "").strip(),
                            (et_img or None), (et_src or None),
                            int(et_page) if et_page else None
                        )
                        st.session_state.wb_edit[iid] = False
                        banner_success("수정되었습니다.")
                        _reload_all()
                    except Exception as e:
                        st.error(f"수정 실패: {e}")
            with b2:
                if st.button("취소", key=f"cancel-{iid}", use_container_width=True):
                    st.session_state.wb_edit[iid] = False
                    st.rerun()
        else:
            st.markdown(f"<div class='card-title'>📝 문제</div>", unsafe_allow_html=True)
            st.markdown(f"{it.get('question','(문항 없음)')}", unsafe_allow_html=True)

            st.markdown("<div class='answer-row'>", unsafe_allow_html=True)
            my_ok = it.get("my_answer") == it.get("correct_answer")
            cls_my = "answer-box answer-good" if my_ok else "answer-box answer-bad"
            cA, cB = st.columns(2)
            with cA:
                st.markdown(f"<div class='{cls_my}'><b>내 답</b><br>{it.get('my_answer','')}</div>", unsafe_allow_html=True)
            with cB:
                st.markdown(f"<div class='answer-box'><b>정답</b><br>{it.get('correct_answer','')}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"<div class='answer-box' style='margin-top:8px'><b>피드백</b><br>{it.get('explanation','')}</div>", unsafe_allow_html=True)

            k1, k2, _ = st.columns([1,1,6])
            with k1:
                if st.button("✏️ 편집", key=f"edit-{iid}", use_container_width=True):
                    st.session_state.wb_edit[iid] = True
                    st.rerun()
            with k2:
                if st.button("🗑 삭제", key=f"del-{iid}", use_container_width=True):
                    try:
                        api_wrong_delete(iid)
                        banner_success("삭제되었습니다.")
                        _reload_all()
                    except Exception as e:
                        st.error(f"삭제 실패: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- 오답 추가 --------------------
st.divider()
with st.expander("➕ 오답 추가"):
    c1, c2 = st.columns([2,1])
    with c1:
        new_date = st.date_input("날짜", value=dt.date.today())
        new_question = st.text_area("문제", placeholder="문항 텍스트")
        new_expl = st.text_area("피드백(해설)", placeholder="왜 틀렸는지, 정리")
        new_src = st.text_input("출처(옵션, 예: OCR/교재명)")
        new_img = st.text_input("이미지 URL(옵션)")
    with c2:
        new_my  = st.text_input("내 답")
        new_cor = st.text_input("정답")
        new_page = st.number_input("페이지(옵션)", min_value=0, value=0)

    if st.button("추가 저장", type="primary"):
        date_key = new_date.strftime("%Y-%m-%d")
        if (new_question or "").strip():
            try:
                api_wrong_add(
                    date_key,
                    (new_question or "").strip(),
                    (new_my or "").strip(),
                    (new_cor or "").strip(),
                    (new_expl or "").strip(),
                    image=(new_img or None),
                    source=(new_src or None),
                    page=int(new_page) if new_page else None
                )
                banner_success("오답이 저장되었습니다.")
                _reload_all()
            except Exception as e:
                st.error(f"저장 실패: {e}")
        else:
            banner_info("문제 내용을 입력해 주세요.")

st.markdown("</div>", unsafe_allow_html=True)