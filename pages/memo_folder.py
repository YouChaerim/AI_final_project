# memo_folder_ui.py
# 메모장 폴더 (메모 JSON 저장 + user_data.json 자동 저장) — 헤더 제거 + 경로 캡션 숨김 + 돌아가기 버튼(헤더 아래 우측)
import streamlit as st
import datetime as dt
import uuid
import urllib.parse
import os, json, tempfile, shutil

st.set_page_config(
    page_title="메모장 폴더 (JSON 저장 + user_data 자동 저장)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= CSS: 최상단 여백 & 사이드바 없애기 =================
st.markdown("""
<style>
/* 기본 상단 UI 제거 */
header[data-testid="stHeader"]{ display:none !important; }
div[data-testid="stToolbar"]{ display:none !important; }
div[data-testid="stDecoration"]{ display:none !important; }
div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }

/* 사이드바 완전 숨김 */
section[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebarContent"]{ display:none !important; }
/* 사이드바 자리 여백 제거 (일부 버전 대응) */
main[data-testid="stAppViewContainer"]{ padding-left:0 !important; }

/* 페이지 상단 여백 제거 */
html, body, .stApp{ margin:0 !important; padding:0 !important; }
main[data-testid="stAppViewContainer"]{ padding-top:0 !important; }
section.main > div.block-container{ padding-top:0 !important; }
div[data-testid="block-container"]{ padding-top:0 !important; padding-bottom:16px !important; }

div[data-testid="stVerticalBlock"] > div:first-child{ margin-top:0 !important; }
h1,h2,h3,h4,h5,h6{ margin-top: 4px !important; margin-bottom: 8px !important; }
p{ margin-top: 4px !important; margin-bottom: 8px !important; }

.container {max-width:1200px; margin:0 auto; padding:0 24px 16px;}
.section-title{
  margin:4px 0 6px 0;
  padding:12px 14px;
  border-radius:14px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff; text-align:center; font-weight:900; font-size:30px;
  box-shadow:0 6px 14px rgba(0,0,0,.06);
}
.note-card{
  background:#fff; border-radius:14px; padding:14px 16px;
  box-shadow:0 6px 14px rgba(0,0,0,.06); margin-bottom:10px;
}
.stTextArea textarea{line-height:1.5}
.small-muted{color:#777; font-size:12px;}

/* --- 저장폴더 이동 버튼 전용 스타일 --- */
#go-folder-bottom + div button {
  background: #fff !important;
  color: #111 !important;
  border: 1px solid rgba(0,0,0,.12) !important;
  padding: 4px 10px !important;
  font-size: 14px !important;
  border-radius: 10px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
#go-folder-bottom + div button:hover {
  background: #fff !important;
  border-color: rgba(0,0,0,.20) !important;
}

/* --- 🔎 검색 버튼(오른쪽) 라인 정렬 --- */
#memo-search-btn + div button{
  height:38px !important;           /* 입력창 높이에 맞춤 */
  margin-top:26px !important;       /* 라벨 높이만큼 내려서 한 줄 정렬 */
  padding:0 16px !important;
  border-radius:10px !important;
  border:1px solid rgba(0,0,0,.12) !important;
  background:#fff !important;
  color:#111 !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
}
#memo-search-btn + div button:hover{
  border-color:rgba(0,0,0,.2) !important;
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

# --- 헤더 바로 아래 오른쪽: "저장폴더로 이동" 버튼 ---
row_left, row_right = st.columns([6, 1])
with row_right:
    st.markdown('<div id="go-folder-bottom"></div>', unsafe_allow_html=True)
if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
    try:
        st.switch_page("pages/folder_page.py")
    except Exception:
        pass

# ================= 상태 초기화 =================
if "ui_notes" not in st.session_state:
    st.session_state.ui_notes = load_notes()
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}

notes_by_date = st.session_state.ui_notes
user_data     = st.session_state.user_data

def _save_user_data_from_state():
    save_user_data(st.session_state.user_data)

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

    # 🔎 검색 입력 + 버튼을 같은 줄에 배치
    s1, s2 = st.columns([7, 1])
    with s1:
        q = st.text_input("제목/내용 검색", placeholder="키워드를 입력하세요…", key="search_q")
    with s2:
        st.markdown('<div id="memo-search-btn"></div>', unsafe_allow_html=True)
        do_search = st.button("검색", key="memo-do-search")
        if do_search:
            st.rerun()

    all_dates = sorted(notes_by_date.keys(), reverse=True)
    sel = st.selectbox("날짜 선택", all_dates, index=0 if all_dates else None)
    day_notes = notes_by_date.get(sel, [])

    if st.session_state.search_q:
        ql = st.session_state.search_q.lower()
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
                        notes_by_date[sel] = [x for x in notes_by_date.get(sel, []) if x["id"] != note_id]
                        if not notes_by_date.get(sel):
                            del notes_by_date[sel]
                        save_notes(notes_by_date)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ================= 마지막 한번 저장 =================
save_user_data(st.session_state.user_data)
