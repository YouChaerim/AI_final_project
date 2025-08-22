# wrongbook_ui.py
# 오답 노트 (OCR 퀴즈 피드백) UI - 날짜별 열람/검색/편집/삭제/복습완료
import streamlit as st
import datetime as dt
import uuid
import json, os, tempfile, shutil

st.set_page_config(
    page_title="오답 노트 (OCR 퀴즈)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

/* 공통 컨테이너 */
.container{ max-width:1200px; margin:0 auto; padding:0 40px 8px; }

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

# ========================= 저장/로드 유틸 =========================
WRONGBOOK_PATH = os.path.join("data", "wrongbook.json")

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def _atomic_write_json(path: str, data: dict):
    _ensure_parent_dir(path)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, path)

def load_wrongbook() -> dict:
    if os.path.exists(WRONGBOOK_PATH):
        try:
            with open(WRONGBOOK_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for d, lst in data.items():
                        for it in lst:
                            it.setdefault("bookmarked", False)  # 데이터 유지(호환), UI 미표시
                            it.setdefault("reviewed", False)
                    return data
        except Exception:
            pass
    today = dt.date.today().strftime("%Y-%m-%d")
    yday  = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        today: [
            {
                "id": str(uuid.uuid4()),
                "quiz_id": "OCR-2025-0819-01",
                "question": "다음 중 광합성에 직접 사용되지 않는 것은?",
                "my_answer": "산소",
                "correct_answer": "이산화탄소",
                "explanation": "광합성은 이산화탄소와 물을 이용해 포도당과 산소를 만든다.",
                "image": None,
                "source": "OCR",
                "page": 3,
                "reviewed": False,
                "bookmarked": False,
                "created_at": dt.datetime.now().isoformat(timespec="seconds"),
                "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        ],
        yday: [
            {
                "id": str(uuid.uuid4()),
                "quiz_id": "OCR-2025-0818-02",
                "question": "삼각형의 내각의 합은?",
                "my_answer": "360°",
                "correct_answer": "180°",
                "explanation": "모든 삼각형의 내각의 합은 180°이다.",
                "image": None,
                "source": "OCR",
                "page": 12,
                "reviewed": True,
                "bookmarked": True,
                "created_at": dt.datetime.now().isoformat(timespec="seconds"),
                "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        ],
    }

def save_wrongbook(data: dict):
    _atomic_write_json(WRONGBOOK_PATH, data)

# ========================= 세션 상태 =========================
if "wrongbook" not in st.session_state:
    st.session_state.wrongbook = load_wrongbook()
if "wb_edit" not in st.session_state:
    st.session_state.wb_edit = {}  # {id: bool}
# 새로 추가 후 성공 문구 노출용 플래그
if "just_added" not in st.session_state:
    st.session_state.just_added = False
if "just_added_date" not in st.session_state:
    st.session_state.just_added_date = None

wb = st.session_state.wrongbook

# ========================= 메인헤더 =========================
st.markdown("""
<div class="container">
  <div class="panel-head">오답 폴더</div>
</div>
""", unsafe_allow_html=True)

# ========================= 헤더 아래 왼쪽: "저장폴더로 이동" 버튼 =========================
st.markdown("<div class='container'>", unsafe_allow_html=True)
row_left, _ = st.columns([1, 6])
with row_left:
    st.markdown('<div id="go-folder-left"></div>', unsafe_allow_html=True)
    if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
        try:
            st.switch_page("pages/folder_page.py")
        except Exception:
            pass

# ========================= 본문 (컨테이너 계속) =========================

# ---- 통계칩
all_items = [(d, it) for d, lst in wb.items() for it in lst]
today_str = dt.date.today().strftime("%Y-%m-%d")
this_week = dt.date.today().isocalendar().week
cnt_total = len(all_items)
cnt_today = sum(1 for d,_ in all_items if d == today_str)
cnt_week  = sum(1 for d,_ in all_items if dt.date(*map(int, d.split("-"))).isocalendar().week == this_week)

st.markdown("<div class='statbar'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="statchip">총 오답: {cnt_total}</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="statchip">오늘: {cnt_today}</div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="statchip">이번 주: {cnt_week}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- 툴바(검색/날짜: 캘린더)
st.markdown("<div class='toolbar'>", unsafe_allow_html=True)

with st.form("searchbar", clear_on_submit=False):
    # 검색(입력+버튼)과 날짜를 2컬럼으로. 검색 컬럼 내부를 다시 2컬럼(입력/버튼)으로 분할.
    col_search, col_date = st.columns([7, 3])

    with col_search:
        st.markdown('<div class="row-label">제목/내용 검색</div>', unsafe_allow_html=True)
        s1, s2 = st.columns([10, 2])
        with s1:
            q_input = st.text_input("", placeholder="키워드…", key="q_input", label_visibility="collapsed")
        with s2:
            do_search = st.form_submit_button("검색", use_container_width=True)

    with col_date:
        st.markdown('<div class="row-label">날짜 선택</div>', unsafe_allow_html=True)
        sel_date_widget = st.date_input("", value=dt.date.today(), format="YYYY-MM-DD",
                                        key="date_input", label_visibility="collapsed")

    if do_search:
        st.session_state.q_committed = q_input
        st.session_state.sel_date_committed = sel_date_widget

st.markdown("</div>", unsafe_allow_html=True)

# 제출값 우선 사용
q = st.session_state.get("q_committed", st.session_state.get("q_input", ""))
_sel_date = st.session_state.get("sel_date_committed", st.session_state.get("date_input", dt.date.today()))
sel_date_str = _sel_date.strftime("%Y-%m-%d")

st.divider()

# ========================= 데이터 필터링 =========================
def match_filter(date_key, it):
    if date_key != sel_date_str:
        return False
    if q:
        qq = q.lower()
        blob = " ".join([
            it.get("question",""), it.get("my_answer",""), it.get("correct_answer",""),
            it.get("explanation","")
        ]).lower()
        if qq not in blob:
            return False
    return True

# 선택 날짜의 아이템(오답 먼저 정렬)
filtered = []
for d in sorted(wb.keys(), reverse=True):
    for it in sorted(
        wb[d],
        key=lambda x: (x.get("my_answer")==x.get("correct_answer"), x.get("updated_at","")),
        reverse=False
    ):
        if match_filter(d, it):
            filtered.append((d, it))

# ========================= 커스텀 배너 =========================
def banner_success(msg: str):
    st.markdown(
        f"<div style='background:#EAF7EE;border:1px solid #D6F0DD;"
        f"color:#1C7C3A;border-radius:8px;padding:12px 14px;font-weight:700;'>"
        f"{msg}</div>", unsafe_allow_html=True
    )

def banner_info(msg: str):
    st.markdown(
        f"<div style='background:#F6F7F9;border:1px solid #E5E7EB;"
        f"color:#344054;border-radius:8px;padding:12px 14px;font-weight:600;'>"
        f"{msg}</div>", unsafe_allow_html=True
    )

# ========================= 출력 =========================
if not filtered:
    if st.session_state.just_added and st.session_state.just_added_date == sel_date_str:
        banner_success("오답이 있습니다. 확인해보세요.!")
        st.session_state.just_added = False
        st.session_state.just_added_date = None
    else:
        banner_info("이 날짜에는 오답이 없습니다. 아래에서 새 오답을 추가해 보세요.")
else:
    if st.session_state.just_added and st.session_state.just_added_date == sel_date_str:
        banner_success("오답이 있습니다. 확인해보세요.!")
        st.session_state.just_added = False
        st.session_state.just_added_date = None

    for d, it in filtered:
        # ---- 카드 렌더러
        def render_card(date_key, it):
            iid = it["id"]
            is_edit = st.session_state.wb_edit.get(iid, False)

            st.markdown('<div class="card">', unsafe_allow_html=True)

            if is_edit:
                et_q = st.text_area("문제", value=it.get("question",""), key=f"q-{iid}")
                c1, c2 = st.columns(2)
                with c1:
                    et_my = st.text_input("내 답", value=it.get("my_answer",""), key=f"my-{iid}")
                    et_src = st.text_input("출처(예: OCR/교재명)", value=it.get("source",""), key=f"src-{iid}")
                with c2:
                    et_cor = st.text_input("정답", value=it.get("correct_answer",""), key=f"cor-{iid}")
                    et_page = st.number_input("페이지(옵션)", min_value=0, value=int(it.get("page") or 0), key=f"page-{iid}")
                et_exp = st.text_area("피드백(해설)", value=it.get("explanation",""), key=f"exp-{iid}")
                et_img = st.text_input("이미지 경로/URL(옵션)", value=it.get("image") or "", key=f"img-{iid}")

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("저장", key=f"save-{iid}", type="primary", use_container_width=True):
                        it.update({
                            "question": et_q, "my_answer": et_my, "correct_answer": et_cor,
                            "explanation": et_exp, "image": et_img or None,
                            "source": et_src, "page": int(et_page) if et_page else None,
                            "updated_at": dt.datetime.now().isoformat(timespec="seconds")
                        })
                        st.session_state.wb_edit[iid] = False
                        save_wrongbook(wb)
                        st.rerun()
                with b2:
                    if st.button("취소", key=f"cancel-{iid}", use_container_width=True):
                        st.session_state.wb_edit[iid] = False
                        st.rerun()
            else:
                st.markdown(f"<div class='card-title'>📝 문제</div>", unsafe_allow_html=True)
                st.markdown(f"{it.get('question','(문항 없음)')}", unsafe_allow_html=True)

                if it.get("image"):
                    st.image(it["image"], use_column_width=False, caption="문항 이미지", output_format="auto")

                st.markdown("<div class='answer-row'>", unsafe_allow_html=True)
                my_ok = it.get("my_answer") == it.get("correct_answer")
                cls_my = "answer-box answer-good" if my_ok else "answer-box answer-bad"
                with st.container():
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
                        wb[date_key] = [x for x in wb.get(date_key, []) if x["id"] != iid]
                        if not wb[date_key]:
                            del wb[date_key]
                        save_wrongbook(wb)
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        render_card(d, it)

# ========================= 수동 입력(간소화) =========================
st.divider()
with st.expander("➕ 오답 추가"):
    c1, c2 = st.columns([2,1])
    with c1:
        new_date = st.date_input("날짜", value=dt.date.today())
        new_question = st.text_area("문제", placeholder="문항 텍스트")
        new_expl = st.text_area("피드백(해설)", placeholder="왜 틀렸는지, 정리")
    with c2:
        new_my = st.text_input("내 답")
        new_cor = st.text_input("정답")

    if st.button("추가 저장", type="primary"):
        key = new_date.strftime("%Y-%m-%d")
        item = {
            "id": str(uuid.uuid4()),
            "quiz_id": f"OCR-{key}-{str(uuid.uuid4())[:8]}",
            "question": new_question.strip(),
            "my_answer": new_my.strip(),
            "correct_answer": new_cor.strip(),
            "explanation": new_expl.strip(),
            "reviewed": False,
            "bookmarked": False,  # 데이터 유지(호환), UI 미사용
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        }
        if item["question"]:
            st.session_state.wrongbook.setdefault(key, []).append(item)
            save_wrongbook(st.session_state.wrongbook)
            st.session_state.just_added = True
            st.session_state.just_added_date = key
            banner_success("오답이 저장되었습니다.")
            st.rerun()
        else:
            banner_info("문제 내용을 입력해 주세요.")

# 컨테이너 닫기
st.markdown("</div>", unsafe_allow_html=True)
