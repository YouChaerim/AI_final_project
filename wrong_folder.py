# wrongbook_ui.py
# 오답 노트 (OCR 퀴즈 피드백) UI - 날짜별 열람/검색/편집/삭제/즐겨찾기/복습완료
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
header[data-testid="stHeader"]{ display:none !important; }
div[data-testid="stToolbar"]{ display:none !important; }
div[data-testid="stDecoration"]{ display:none !important; }
div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }

/* 2) 컨테이너 상단 패딩 0 */
[data-testid="stAppViewContainer"]{ padding-top:0 !important; }
div[data-testid="block-container"],
div[class*="block-container"]{ padding-top:0 !important; padding-bottom:12px !important; }

/* 3) 첫 요소 margin-top 0 (margin-collapsing 방지) */
div[data-testid="block-container"] > div:first-child{ margin-top:0 !important; padding-top:0 !important; }
h1,h2,h3,h4,h5,h6{ margin-top:0 !important; }

/* 공통 컨테이너: 상단 패딩 0으로 더 붙임 */
.container{ max-width:1200px; margin:0 auto; padding:0 40px 8px; }

/* 메인헤더(오렌지 그라데이션 바) - 상단 여백 제거 */
.panel-head{
  margin-top:0;
  border-radius:18px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff;
  font-size:28px; font-weight:900; text-align:center;
  padding:16px 20px;
  box-shadow:0 8px 18px rgba(0,0,0,.06);
}

/* 통계칩 / 툴바: 위쪽 마진 최소화 */
.statbar{display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 8px 0;}
.statchip{
  background:#FFFFFF; border-radius:12px; padding:8px 10px;
  box-shadow:0 2px 10px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06);
  font-weight:800; font-size:14px;
}
.toolbar{display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin:0 0 6px 0;}
label{ font-size:0.92rem !important; margin-bottom:2px !important; }

/* 칩 */
.pill{display:inline-block; padding:6px 10px; border-radius:999px; background:#F6F7F9; font-size:12px; color:#555; margin-right:6px;}
.pill.src{background:#eef3ff; color:#1b3c8c;}

/* 카드 */
.card{
  background:#FFFFFF; border-radius:16px; padding:14px 16px;
  box-shadow:0 8px 18px rgba(0,0,0,.06); margin-bottom:10px; border:1px solid rgba(0,0,0,.06);
}
.card-header{display:flex; justify-content:space-between; align-items:center; gap:8px;}
.card-title{font-weight:800; font-size:16px; margin-bottom:6px;}
.card-meta{font-size:12px; color:#666;}

/* 답변 박스 */
.answer-row{display:flex; gap:12px; align-items:flex-start; flex-wrap:wrap}
.answer-box{ flex:1 1 280px; border-radius:12px; padding:10px 12px; border:1px solid #eee; background:#fafafa; }
.answer-good{ border-color:#d4f5d4; background:#f6fff6; }
.answer-bad{  border-color:#ffd6d6; background:#fff6f6; }

/* 이미지 */
img.qimg{border-radius:12px; border:1px solid rgba(0,0,0,.06); max-height:240px; object-fit:contain}

/* 저장폴더 이동 버튼(헤더 왼쪽 밑) 스타일 */
#go-folder-left + div button{
  background:#fff !important;
  color:#111 !important;
  border:1px solid rgba(0,0,0,.12) !important;
  padding:4px 10px !important;
  font-size:14px !important;
  border-radius:10px !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
}
#go-folder-left + div button:hover{
  border-color:rgba(0,0,0,.2) !important;
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
                            it.setdefault("bookmarked", False)
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
    # 이 마커 바로 다음 생성되는 첫 버튼을 CSS로 스타일링
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
cnt_star  = sum(1 for _,it in all_items if it.get("bookmarked"))

st.markdown("<div class='statbar'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="statchip">총 오답: {cnt_total}</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="statchip">오늘: {cnt_today}</div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="statchip">이번 주: {cnt_week}</div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="statchip">즐겨찾기: {cnt_star}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- 툴바(검색/날짜: 캘린더)
st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
t1, t2 = st.columns([2,1])
with t1:
    q = st.text_input("제목/내용 검색", placeholder="키워드…")
with t2:
    sel_date = st.date_input("날짜 선택", value=dt.date.today(), format="YYYY-MM-DD")
    sel_date_str = sel_date.strftime("%Y-%m-%d") if isinstance(sel_date, dt.date) else str(sel_date)
st.markdown("</div>", unsafe_allow_html=True)

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

# ========================= 액션 유틸 =========================
def _save_and_rerun():
    save_wrongbook(wb)
    st.rerun()

def toggle_bookmark(date_key, item_id):
    for it in wb.get(date_key, []):
        if it["id"] == item_id:
            it["bookmarked"] = not it.get("bookmarked", False)
            it["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
            break
    _save_and_rerun()

def toggle_reviewed(date_key, item_id, val: bool):
    for it in wb.get(date_key, []):
        if it["id"] == item_id:
            it["reviewed"] = bool(val)
            it["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
            break
    save_wrongbook(wb)

def delete_item(date_key, item_id):
    wb[date_key] = [x for x in wb.get(date_key, []) if x["id"] != item_id]
    if not wb[date_key]:
        del wb[date_key]
    _save_and_rerun()

# ========================= 카드 렌더러 =========================
def render_card(date_key, it):
    iid = it["id"]
    is_edit = st.session_state.wb_edit.get(iid, False)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    # 헤더 라인: 칩 + 메타 + 즐겨찾기
    h1, h2, h3 = st.columns([5, 2, 1])
    with h1:
        chips = [f"<span class='pill'>{date_key}</span>"]
        if it.get("source"): chips.append(f"<span class='pill src'>{it.get('source')}</span>")
        if it.get("page") is not None: chips.append(f"<span class='pill'>p.{it.get('page')}</span>")
        st.markdown(" ".join(chips), unsafe_allow_html=True)
    with h2:
        st.caption(f"ID: {it.get('quiz_id','-')}")
        st.caption(f"업데이트: {it.get('updated_at','-')}")
    with h3:
        star = "★" if it.get("bookmarked") else "☆"
        if st.button(star, key=f"star-{iid}", help="즐겨찾기", use_container_width=True):
            toggle_bookmark(date_key, iid)

    st.markdown("---")

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
                _save_and_rerun()
        with b2:
            if st.button("취소", key=f"cancel-{iid}", use_container_width=True):
                st.session_state.wb_edit[iid] = False
                st.rerun()
    else:
        # 문제
        st.markdown(f"<div class='card-title'>📝 문제</div>", unsafe_allow_html=True)
        st.markdown(f"{it.get('question','(문항 없음)')}", unsafe_allow_html=True)

        # 이미지(있을 때만)
        if it.get("image"):
            st.image(it["image"], use_column_width=False, caption="문항 이미지", output_format="auto")

        # 정답/내 답
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

        # 피드백(해설) 항상 보이기
        st.markdown(f"<div class='answer-box' style='margin-top:8px'><b>피드백</b><br>{it.get('explanation','')}</div>", unsafe_allow_html=True)

        # 액션
        k1, k2, k3, _ = st.columns([1,1,1,3])
        with k1:
            if st.button("✏️ 편집", key=f"edit-{iid}", use_container_width=True):
                st.session_state.wb_edit[iid] = True
                st.rerun()
        with k2:
            if st.button("🗑 삭제", key=f"del-{iid}", use_container_width=True):
                delete_item(date_key, iid)
        with k3:
            reviewed = st.checkbox("복습 완료", value=bool(it.get("reviewed")), key=f"rev-{iid}")
            toggle_reviewed(date_key, iid, reviewed)

    st.markdown("</div>", unsafe_allow_html=True)

# ========================= 출력 =========================
st.markdown(f"### {sel_date_str}")
if not filtered:
    st.info("이 날짜에는 오답이 없습니다. 아래에서 새 오답을 추가해 보세요.")
else:
    for d, it in filtered:
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
            # page/source/image 필드 생성하지 않음
            "reviewed": False,
            "bookmarked": False,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
        }
        if item["question"]:
            st.session_state.wrongbook.setdefault(key, []).append(item)
            save_wrongbook(st.session_state.wrongbook)  # 자동 저장
            st.success("오답이 저장되었습니다.")
            st.rerun()
        else:
            st.warning("문제 내용을 입력해 주세요.")

# 컨테이너 닫기
st.markdown("</div>", unsafe_allow_html=True)
