# memo_folder_ui.py
# 메모장 폴더 (메모 JSON 저장 + user_data.json 자동 저장)
import streamlit as st
import datetime as dt
import uuid
import os, json, tempfile, shutil

st.set_page_config(
    page_title="메모장 폴더 (JSON 저장 + user_data 자동 저장)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= CSS =================
st.markdown("""
<style>
/* 기본 상단 UI 제거 */
header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }

/* 사이드바 숨김 + 여백 제거 */
section[data-testid="stSidebar"], div[data-testid="stSidebar"],
div[data-testid="stSidebarContent"]{ display:none !important; }
main[data-testid="stAppViewContainer"]{ padding-left:0 !important; padding-top:0 !important; }
div[data-testid="block-container"]{ padding-top:0 !important; padding-bottom:16px !important; }

/* 공용 레이아웃 */
.container {max-width:1200px; margin:0 auto; padding:0 24px 16px;}
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

/* 저장폴더 이동 버튼 */
#go-folder-bottom + div button{
  background:#fff !important; color:#111 !important;
  border:1px solid rgba(0,0,0,.12) !important; padding:4px 10px !important;
  font-size:14px !important; border-radius:10px !important; box-shadow:0 1px 2px rgba(0,0,0,.04);
}
#go-folder-bottom + div button:hover{ border-color:rgba(0,0,0,.2) !important; }

/* -------- 검색 줄: 입력/버튼/날짜 크기 & 정렬 완전 일치 -------- */
.row-label{ font-size:0.92rem; font-weight:600; margin:0 0 6px 0; color:#344054; }

/* 원하는 공통 높이/라운드 한번에 조절 */
:root{
  --search-h: 44px;   /* ← 여기만 바꾸면 셋 다 같이 바뀜 */
  --search-r: 12px;
  --search-pad-x: 14px;
}

/* 1) 검색 입력 */
#search-input-anchor + div input{
  height:var(--search-h) !important;
  border-radius:var(--search-r) !important;
  padding:0 var(--search-pad-x) !important;
  box-sizing:border-box !important;
}

/* 2) 검색 버튼 */
#search-btn-anchor + div button{
  height:var(--search-h) !important;
  border-radius:var(--search-r) !important;
  padding:0 var(--search-pad-x) !important;
  font-weight:800 !important;
  margin-top:0 !important;
  width:100% !important;
}

/* 3) 날짜 입력(단일 날짜) */
#date-input-anchor + div input{
  height:var(--search-h) !important;
  border-radius:var(--search-r) !important;
  padding:0 var(--search-pad-x) !important;
  box-sizing:border-box !important;
}

/* 컬럼 사이 간격이 너무 넓게 보일 때 조금 조밀하게 */
div[data-testid="column"] > div:has(#search-input-anchor),
div[data-testid="column"] > div:has(#search-btn-anchor),
div[data-testid="column"] > div:has(#date-input-anchor){
  margin-bottom:0 !important;
}
</style>
""", unsafe_allow_html=True)

# ================= 경로/저장 유틸 =================
PROJECT_FOLDER_NAME = "AI_final_project"
NOTES_JSON_PATH = os.path.join("data", "memo_notes.json")

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def _atomic_write_json(path: str, data: dict):
    _ensure_parent_dir(path)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)

def _resolve_user_data_path() -> str:
    cwd = os.path.abspath(os.getcwd())
    if os.path.basename(cwd) == PROJECT_FOLDER_NAME:
        return os.path.join(cwd, "user_data.json")
    cur = cwd
    while True:
        candidate = os.path.join(cur, PROJECT_FOLDER_NAME)
        if os.path.isdir(candidate):
            return os.path.join(candidate, "user_data.json")
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.join(cwd, PROJECT_FOLDER_NAME, "user_data.json")

USER_DATA_PATH = _resolve_user_data_path()

def load_notes() -> dict:
    if os.path.exists(NOTES_JSON_PATH):
        try:
            with open(NOTES_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): list(v) for k, v in data.items()}
        except Exception:
            pass
    today = dt.date.today().strftime("%Y-%m-%d")
    yday  = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        today: [
            {"id": str(uuid.uuid4()), "title": "할 일 점검",
             "content": "- 모델 학습 로그 정리\n- 팀 회의 안건 준비", "updated": "오늘"},
            {"id": str(uuid.uuid4()), "title": "아이디어 스케치",
             "content": "집중도 차트 툴팁 개선 메모", "updated": "오늘"},
        ],
        yday: [
            {"id": str(uuid.uuid4()), "title": "회의 메모",
             "content": "UI 색상 팔레트 확정. 버튼 라운드 14px.", "updated": "어제"},
        ],
    }

def save_notes(data: dict):
    _atomic_write_json(NOTES_JSON_PATH, data)

USER_DATA_DEFAULT = {
    "todo": "", "memo": "", "study_hour": 0, "study_minute": 0,
    "dark_mode": False, "active_char": "rabbit", "owned_hats": [],
    "equipped_hat": None, "todo_items": [], "nickname": "-", "coins": 0, "mode": "ranking",
}

def load_user_data() -> dict:
    path = USER_DATA_PATH
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = {**USER_DATA_DEFAULT, **data}
                    if not isinstance(merged.get("todo_items"), list):
                        merged["todo_items"] = []
                    return merged
        except Exception:
            pass
    return USER_DATA_DEFAULT.copy()

def save_user_data(data: dict):
    merged = {**USER_DATA_DEFAULT, **(data or {})}
    _atomic_write_json(USER_DATA_PATH, merged)

# ================= 페이지 시작 =================
st.markdown('<div class="container">', unsafe_allow_html=True)

# --- 타이틀 ---
st.markdown('<div class="section-title">메모장 폴더</div>', unsafe_allow_html=True)

# --- 헤더 아래 오른쪽: "저장폴더로 이동" 버튼 ---
row_left, row_right = st.columns([6, 1])
with row_right:
    st.markdown('<div id="go-folder-bottom"></div>', unsafe_allow_html=True)
if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
    try:
        st.switch_page("pages/folder_page.py")
    except Exception:
        pass

# ================= 상태 =================
if "ui_notes" not in st.session_state:
    st.session_state.ui_notes = load_notes()
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}
if "q_committed" not in st.session_state:
    st.session_state.q_committed = ""
if "sel_date_committed" not in st.session_state:
    st.session_state.sel_date_committed = None

notes_by_date = st.session_state.ui_notes
user_data     = st.session_state.user_data

# ================= 레이아웃 =================
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("✍️ 새 메모")
    pick_date = st.date_input("날짜", value=dt.date.today(), format="YYYY-MM-DD")
    title = st.text_input("제목", placeholder="예) 오늘 회의 메모")
    content = st.text_area("내용", height=160, placeholder="내용을 입력하세요…")

    if st.button("추가", type="primary", use_container_width=True):
        if (title or "").strip() or (content or "").strip():
            key = pick_date.strftime("%Y-%m-%d")
            notes_by_date.setdefault(key, []).append({
                "id": str(uuid.uuid4()),
                "title": (title or "").strip() or "제목 없음",
                "content": (content or "").strip(),
                "updated": "방금",
            })
            save_notes(notes_by_date)
            user_data["memo"] = f"{(title or '').strip()}\n{(content or '').strip()}".strip()
            save_user_data(user_data)
            st.success("추가되었습니다. (메모/유저 데이터 저장 완료)")
            st.rerun()
        else:
            st.warning("제목 또는 내용을 입력하세요.")

with right:
    st.subheader("📅 날짜별 메모")

    # 캘린더 범위
    if notes_by_date:
        date_keys = sorted([dt.datetime.strptime(k, "%Y-%m-%d").date() for k in notes_by_date], reverse=True)
        min_date = min(date_keys); max_date = max(date_keys)
        default_date = st.session_state.sel_date_committed or date_keys[0]
    else:
        date_keys = []; min_date = max_date = default_date = dt.date.today()

    # ===== 검색줄 (입력/버튼/날짜) =====
    with st.form("memo_search", clear_on_submit=False):
        col_text, col_btn, col_date = st.columns([7, 1.2, 3])

        with col_text:
            st.markdown('<div class="row-label">제목/내용 검색</div>', unsafe_allow_html=True)
            st.markdown('<div id="search-input-anchor"></div>', unsafe_allow_html=True)
            q_input = st.text_input("", placeholder="키워드를 입력하세요…",
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

    # 제출값 우선
    q = st.session_state.q_committed or st.session_state.get("q_input", "")
    sel_date = st.session_state.sel_date_committed or st.session_state.get("date_input", default_date)
    sel_key = sel_date.strftime("%Y-%m-%d")

    # 데이터 필터
    day_notes = notes_by_date.get(sel_key, [])
    if q:
        ql = q.lower()
        day_notes = [n for n in day_notes
                     if ql in n.get("title","").lower() or ql in n.get("content","").lower()]

    if not day_notes:
        st.info("이 날짜에는 메모가 없습니다. 왼쪽에서 새 메모를 추가해 보세요.")
    else:
        for n in list(day_notes)[::-1]:
            note_id = n["id"]
            st.markdown('<div class="note-card">', unsafe_allow_html=True)
            col_content, col_save, col_cancel = st.columns([4, 1, 1])

            if st.session_state.edit_mode.get(note_id, False):
                with col_content:
                    et = st.text_input("제목", value=n["title"], key=f"title-{note_id}")
                    ec = st.text_area("내용", value=n["content"], height=150, key=f"content-{note_id}")
                with col_save:
                    if st.button("변경 적용", key=f"save-{note_id}", type="primary", use_container_width=True):
                        n["title"] = (et or "제목 없음").strip()
                        n["content"] = ec
                        n["updated"] = "방금"
                        save_notes(notes_by_date)
                        user_data["memo"] = f"{n['title']}\n{n['content']}".strip()
                        save_user_data(user_data)
                        st.session_state.edit_mode[note_id] = False
                        st.rerun()
                with col_cancel:
                    if st.button("취소", key=f"cancel-{note_id}", use_container_width=True):
                        st.session_state.edit_mode[note_id] = False
                        st.rerun()
            else:
                with col_content:
                    st.markdown(f"**{n.get('title','제목 없음')}**")
                    st.caption(f"마지막 수정: {n.get('updated','-')}")
                    st.write(n.get("content") or " ")
                with col_save:
                    if st.button("✏️ 수정", key=f"edit-{note_id}", use_container_width=True):
                        st.session_state.edit_mode[note_id] = True
                        st.rerun()
                with col_cancel:
                    if st.button("🗑️ 삭제", key=f"del-{note_id}", use_container_width=True):
                        notes_by_date[sel_key] = [x for x in notes_by_date.get(sel_key, []) if x["id"] != note_id]
                        if not notes_by_date.get(sel_key):
                            del notes_by_date[sel_key]
                        save_notes(notes_by_date)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# 마지막 저장
save_user_data(st.session_state.user_data)
