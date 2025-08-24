# pages/mainpage.py
import os, re, base64, requests
import streamlit as st
from components.header import render_header
from components.auth import require_login

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")
require_login(BACKEND_URL)

user = st.session_state.get("user", {}) or {}
USER_ID = user.get("id") or user.get("_id") or user.get("user_id") or ""

if not USER_ID:
    st.error("세션에 사용자 정보가 없습니다. 다시 로그인해 주세요.")
    st.switch_page("onboarding.py")
    st.stop()

# 세션 기본값
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "todo_items": [],
        "memo": "",
        "study_hour": 0,
        "study_minute": 0,
        "dark_mode": False,
        "active_char": "rabbit",
        "owned_hats": [],
        "equipped_hat": None,
    }
ud = st.session_state.user_data

# -------------------------------
# 1) 유틸
# -------------------------------
def _parse_lines(text: str) -> list[str]:
    if not text: return []
    parts = re.split(r"[\n,;]+", text.strip())
    parts = [re.sub(r"^\s*[-*•\d\.\)]\s*", "", p).strip() for p in parts]
    return [p for p in parts if p]

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        import base64
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def _assets_root():
    here = os.path.dirname(__file__)
    for p in [os.path.abspath(os.path.join(here, "assets")),
              os.path.abspath(os.path.join(here, "..", "assets"))]:
        if os.path.isdir(p): return p
    return os.path.abspath(os.path.join(here, "assets"))
ASSETS_ROOT = _assets_root()

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    cands = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                cands += [
                    os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"),
                    os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"),
                ]
    for k in keys:
        cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))
    for p in cands:
        if os.path.exists(p): return _to_data_uri(p)
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
            "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>")

def current_avatar_uri() -> str:
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    if hat_id and hat_id in ud.get("owned_hats", []):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key)

# -------------------------------
# 2) 서버 연동: 오늘 할 일 + 메모
# -------------------------------
if "new_todos_draft" not in st.session_state:
    st.session_state.new_todos_draft = ""

def _on_click_add_new_todos():
    texts = _parse_lines(st.session_state.get("new_todos_draft", ""))
    if texts:
        add_new_todos(texts)   # 내부에서 fetch_today_todos() 호출됨
    st.session_state.new_todos_draft = ""

def fetch_today_todos():
    """오늘 할 일 전체를 서버에서 가져와 세션에 반영."""
    try:
        r = requests.get(f"{BACKEND_URL}/todos/{USER_ID}", timeout=10)
        r.raise_for_status()
        ud["todo_items"] = [
            {"id": t["id"], "text": t["contents"], "done": t["complete"]}
            for t in r.json()
        ]
    except requests.exceptions.RequestException as e:
        ud.setdefault("todo_items", [])
        st.error(f"오늘 할 일 불러오기 실패: {getattr(e, 'response', None) and e.response.text or e}")

def toggle_todo(todo_id: str, idx: int, new_val: bool):
    try:
        requests.put(f"{BACKEND_URL}/todos/toggle/{USER_ID}/{todo_id}", timeout=10).raise_for_status()
        ud["todo_items"][idx]["done"] = new_val
    except requests.exceptions.RequestException:
        st.error("상태 변경 실패")

def add_new_todos(new_texts: list[str]):
    """신규 항목들만 생성(백엔드가 중복은 무시하거나 신규만 추가하도록 구성)."""
    payload = {"todo_items": [{"text": t} for t in new_texts if t.strip()]}
    if not payload["todo_items"]:
        return
    try:
        requests.post(f"{BACKEND_URL}/todos/{USER_ID}", json=payload, timeout=10).raise_for_status()
        fetch_today_todos()
        st.success("새 할 일이 추가되었습니다.")
    except requests.exceptions.RequestException as e:
        st.error(f"추가 실패: {getattr(e, 'response', None) and e.response.text or e}")

def update_todo_text(todo_id: str, new_text: str):
    """기존 항목 텍스트 수정 (백엔드: PUT /todos/update/{user_id}/{todo_id})."""
    new_text = new_text.strip()
    if not new_text:
        st.warning("내용이 비어있습니다.")
        return
    try:
        requests.put(
            f"{BACKEND_URL}/todos/update/{USER_ID}/{todo_id}",
            json={"text": new_text},
            timeout=10
        ).raise_for_status()
        fetch_today_todos()
        st.success("수정되었습니다.")
    except requests.exceptions.RequestException as e:
        st.error(f"수정 실패: {getattr(e, 'response', None) and e.response.text or e}")

def fetch_memo():
    try:
        r = requests.get(f"{BACKEND_URL}/memos/{USER_ID}", timeout=10)
        r.raise_for_status()
        ud["memo"] = r.json().get("contents", "")
    except requests.exceptions.RequestException as e:
        ud.setdefault("memo", "")
        st.error(f"메모 불러오기 실패: {getattr(e, 'response', None) and e.response.text or e}")

def save_memo(new_text: str):
    try:
        requests.post(
            f"{BACKEND_URL}/memos/{USER_ID}",
            json={"contents": new_text},
            timeout=10
        ).raise_for_status()
        ud["memo"] = new_text
        st.success("메모가 저장되었습니다.")
    except requests.exceptions.RequestException as e:
        st.error(f"메모 저장 실패: {getattr(e, 'response', None) and e.response.text or e}")

# 진입 시 항상 최신 동기화
fetch_today_todos()
fetch_memo()

# -------------------------------
# 3) 스타일 & 헤더
# -------------------------------
bg_color, font_color, card_bg, nav_bg, dark_orange, label_color = \
    "#FAFAFA", "#333", "white", "rgba(255,255,255,0.9)", "#FF9330", "#333"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

:root{
  --bg:#FAFAFA;
  --text:#333;
  --nav:rgba(255,255,255,0.9);
  --card:#fff;
  --label:#333;
  --accent:#FF9330;
  --border:rgba(0,0,0,0.06);
}

/* 기본 */
html,body{ background:var(--bg); color:var(--text); font-family:'Noto Sans KR',sans-serif; zoom:1.10; margin:0; }
.stApp{ background:var(--bg); }
.block-container{ padding-top:10px !important; }
.container{ max-width:1200px; margin:auto; padding:40px; }
a{ color:var(--text); text-decoration:none !important; }

/* 스트림릿 UI 숨김 */
[data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stToolbar"]{ display:none !important; }
            
/* 메인 히어로 박스 */
.main-box{
  background:var(--accent);
  border-radius:14px;
  padding:90px 0 140px 0;
  text-align:center;
  color:#fff;
  font-size:36px;
  font-weight:900;
  margin-bottom:16px;
}

/* "공부 시작" 버튼 (switch_page 버튼) */
.main-box .stButton > button{
  margin-top:30px;
  padding:16px 40px;
  background:#fff;
  color:#000 !important;
  font-weight:800;
  border:none;
  border-radius:8px;
  font-size:22px;
  cursor:pointer;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
}
.main-box .stButton > button:hover{ filter:brightness(.98); }

/* st.page_link를 버튼처럼 (전역) */
[data-testid="stPageLink"] > a{
  display:inline-block;
  margin-top:30px;
  padding:16px 40px;
  background:#fff;
  color:#000 !important;
  font-weight:800;
  border-radius:8px;
  font-size:22px;
  text-decoration:none !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
}
[data-testid="stPageLink"] > a:hover{ filter:brightness(.98); }

/* 카드/익스팬더 */
div[data-testid="stExpander"]{
  background:var(--card);
  border-radius:10px;
  border:1px solid #eee;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
  overflow:hidden;
  margin:1px 0 !important;
}

/* 라벨 */
label{ color:var(--label) !important; font-weight:600; }

/* 유틸 */
.right-col-align{ position:relative; top:-4px; }
.tight-stack > * + *{ margin-top:8px; }
header{ display:none !important; }
</style>
""", unsafe_allow_html=True)


render_header()

# -------------------------------
# 4) 본문
# -------------------------------
st.markdown('<div class="container">', unsafe_allow_html=True)

left, right = st.columns([2.5, 1])
with left:
    st.markdown(
        """
        <div class="main-box">
          오늘 공부 시작하기
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/main.py", label="공부 시작")

with right:
    st.markdown('<div class="right-col-align tight-stack">', unsafe_allow_html=True)

    # 보기 모드
    if not st.session_state.edit_mode:
        with st.expander("📌 오늘 할 일", expanded=True):
            todos = ud.get("todo_items", [])
            if not todos:
                st.caption("오늘 등록된 할 일이 없습니다.")
            for i, item in enumerate(todos):
                checked = st.checkbox(item["text"], value=item["done"], key=f"todo_view_{item['id']}")
                if checked != item["done"]:
                    toggle_todo(item["id"], i, checked)
                    st.rerun()

        with st.expander("🗓 빠른 메모", expanded=True):
            st.write(ud.get("memo", ""))

        with st.expander("⏰ 오늘 공부시간", expanded=True):
            st.write(f"{ud.get('study_hour', 0)}시간 {ud.get('study_minute', 0)}분")

        if st.button("✏️ 변경하기", use_container_width=True):
            st.session_state.edit_mode = True
            st.rerun()

    # 편집 모드
    else:
        # 4-1) 새 항목 추가
        with st.expander("➕ 새 항목 추가 (한 줄에 하나씩)", expanded=True):
            st.text_area(
                "새 할 일",
                key="new_todos_draft",
                placeholder="예) 영어 단어 30개\n수학 문제 5개",
                height=140
            )
            st.button(
                "추가하기",
                use_container_width=True,
                on_click=_on_click_add_new_todos,   # ← 여기서 처리
            )

        # 4-2) 기존 항목 수정
        with st.expander("✍️ 기존 항목 수정", expanded=True):
            todos = ud.get("todo_items", [])
            if not todos:
                st.caption("오늘 등록된 할 일이 없습니다.")
            for item in todos:
                with st.form(key=f"form_edit_{item['id']}"):
                    new_text = st.text_input("내용", value=item["text"], key=f"edit_{item['id']}")
                    cols = st.columns([1, 3])
                    with cols[0]:
                        submitted = st.form_submit_button("저장")
                    with cols[1]:
                        st.caption("수정 후 저장을 누르면 바로 반영됩니다.")
                    if submitted and new_text != item["text"]:
                        update_todo_text(item["id"], new_text)
                        st.rerun()

        # 4-3) 메모 수정
        with st.expander("🗓 빠른 메모 수정", expanded=True):
            memo_text = st.text_area("메모", value=ud.get("memo", ""), height=120, key="edit_memo_text")
            if st.button("메모 저장", use_container_width=True):
                save_memo(memo_text)
                st.rerun()

        # 4-4) 편집 종료
        if st.button("✅ 편집 완료", use_container_width=True):
            st.session_state.edit_mode = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
