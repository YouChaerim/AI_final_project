# pdf_folder_ui.py
# PDF 폴더 - 날짜별 저장/열람/검색/미리보기/바로사용  (즐겨찾기 제거)
import streamlit as st
import datetime as dt
import uuid, json, os, tempfile, shutil, base64

# ------------------------ 페이지 기본 ------------------------
st.set_page_config(
    page_title="PDF 폴더",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------ 스타일 (오답 노트와 동일 위치/여백) ------------------------
st.markdown("""
<style>
/* 루트/헤더 여백 완전 제거 */
html, body { margin:0 !important; padding:0 !important; }
main.stApp{ padding-top:0 !important; }
header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }

/* 사이드바 완전 숨김 + 좌측 여백 제거 */
section[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebar"]{ display:none !important; }
div[data-testid="stSidebarContent"]{ display:none !important; }
[data-testid="stAppViewContainer"]{ padding-left:0 !important; padding-top:0 !important; }

div[data-testid="block-container"], div[class*="block-container"]{
  padding-top:0 !important; padding-bottom:12px !important;
}
div[data-testid="block-container"] > div:first-child{ margin-top:0 !important; padding-top:0 !important; }
h1,h2,h3,h4,h5,h6{ margin-top:0 !important; }

/* 공통 컨테이너/헤더 */
.container{ max-width:1200px; margin:0 auto; padding:0 40px 8px; }
.panel-head{
  margin-top:0;
  border-radius:18px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff;
  font-size:28px; font-weight:900; text-align:center;
  padding:16px 20px;
  box-shadow:0 8px 18px rgba(0,0,0,.06);
}

/* 통계칩/툴바/칩 */
.statbar{display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 8px 0;}
.statchip{
  background:#fff; border-radius:12px; padding:8px 10px;
  box-shadow:0 2px 10px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06);
  font-weight:800; font-size:14px;
}
.toolbar{display:flex; gap:10px; align-items:end; flex-wrap:wrap; margin:0 0 6px 0;}
label{ font-size:0.92rem !important; margin-bottom:2px !important; }
.pill{display:inline-block; padding:6px 10px; border-radius:999px; background:#F6F7F9; font-size:12px; color:#555; margin-right:6px;}
.pill.src{background:#eef3ff; color:#1b3c8c;}
.pill.use{background:#eaf8ff; color:#125;}

/* 카드 */
.card{
  background:#fff; border-radius:16px; padding:14px 16px;
  box-shadow:0 8px 18px rgba(0,0,0,.06); margin-bottom:10px; border:1px solid rgba(0,0,0,.06);
}
.card-header{display:flex; justify-content:space-between; align-items:center; gap:8px;}
.card-title{font-weight:800; font-size:16px; margin-bottom:6px;}
.card-meta{font-size:12px; color:#666;}
.card-actions{display:flex; gap:8px; flex-wrap:wrap}

/* PDF 미리보기 영역 */
.preview-box{ border:1px solid #eee; border-radius:12px; overflow:hidden; background:#fafafa; }

/* 업로더 가독성 */
.upload-note{ font-size:12px; color:#666; margin-top:4px; }

/* 메인헤더 아래 왼쪽 버튼 스타일 */
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

/* 🔎 검색 버튼을 검색창과 같은 라인에 정렬 */
#search-btn + div button{
  height:38px !important;            /* 입력창 높이에 맞춤 */
  margin-top:26px !important;        /* 라벨 높이만큼 내려서 수평 정렬 */
  padding:0 16px !important;
  border-radius:10px !important;
  border:1px solid rgba(0,0,0,.12) !important;
  background:#fff !important;
  color:#111 !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
}
#search-btn + div button:hover{
  border-color:rgba(0,0,0,.2) !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------ 경로/저장 유틸 ------------------------
INDEX_PATH = os.path.join("data", "pdf_folder_index.json")
STORE_DIR  = os.path.join("data", "pdfs")

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent: os.makedirs(parent, exist_ok=True)

def _atomic_write_json(path: str, data: dict):
    _ensure_parent_dir(path)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, path)

def _save_bytes(path: str, content: bytes):
    _ensure_parent_dir(path)
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(content)
        tpath = tmp.name
    os.replace(tpath, path)

def load_index() -> dict:
    """{date: [items...]} 구조"""
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for d, lst in data.items():
                        for it in lst:
                            # 즐겨찾기 제거 이후 호환: 필요한 필드 기본값 보정
                            it.setdefault("notes", "")
                            it.setdefault("title", it.get("original_name","PDF"))
                    return data
        except Exception:
            pass
    return {}

def save_index(data: dict):
    _atomic_write_json(INDEX_PATH, data)

def human_size(n: int) -> str:
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.0f}{unit}" if unit=="B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"

# ------------------------ 세션 ------------------------
if "pdf_index" not in st.session_state:
    st.session_state.pdf_index = load_index()
if "pdf_edit" not in st.session_state:
    st.session_state.pdf_edit = {}  # {id: bool}
if "pdf_use" not in st.session_state:
    st.session_state.pdf_use = None  # 선택된 PDF id

idx = st.session_state.pdf_index

# ------------------------ 헤더 ------------------------
st.markdown("""
<div class="container">
  <div class="panel-head">PDF 폴더</div>
</div>
""", unsafe_allow_html=True)

# ------------------------ 메인헤더 아래 왼쪽: 저장폴더로 이동 버튼 ------------------------
st.markdown("<div class='container'>", unsafe_allow_html=True)
btn_left, _ = st.columns([1, 6])
with btn_left:
    st.markdown('<div id="go-folder-left"></div>', unsafe_allow_html=True)
    if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
        try:
            st.switch_page("pages/folder_page.py")
        except Exception:
            pass

# ------------------------ 통계칩 ------------------------
all_items = [(d, it) for d, lst in idx.items() for it in lst]
today_str = dt.date.today().strftime("%Y-%m-%d")
this_week  = dt.date.today().isocalendar().week

cnt_total = len(all_items)
cnt_today = sum(1 for d,_ in all_items if d == today_str)
cnt_week  = sum(1 for d,_ in all_items if dt.date(*map(int, d.split("-"))).isocalendar().week == this_week)

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="statchip">총 파일: {cnt_total}</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="statchip">오늘: {cnt_today}</div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="statchip">이번 주: {cnt_week}</div>', unsafe_allow_html=True)

# ------------------------ 툴바 (검색 + 날짜 캘린더) ------------------------
t1, t2 = st.columns([2,1])

with t1:
    # 검색창과 검색 버튼을 같은 라인에 배치
    s1, s2 = st.columns([7, 1])
    with s1:
        q = st.text_input("제목/메모/파일명 검색", placeholder="키워드…")
    with s2:
        # 버튼을 라벨 아래로 자연스럽게 내리기 위한 앵커 + CSS
        st.markdown('<div id="search-btn"></div>', unsafe_allow_html=True)
        do_search = st.button("검색", key="do-search")

        # 버튼 클릭 시 즉시 필터 적용 (Streamlit은 버튼 클릭으로도 rerun 되지만 명시적으로 처리)
        if do_search:
            st.rerun()

with t2:
    pick_date = st.date_input("날짜 선택", value=dt.date.today(), format="YYYY-MM-DD")
    sel_date_str = pick_date.strftime("%Y-%m-%d")

st.divider()

# ------------------------ 업로드 ------------------------
with st.expander("➕ PDF 추가"):
    up_files = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
    st.markdown('<div class="upload-note">여러 개 선택 가능 · 저장 시 오늘 날짜로 자동 분류됩니다.</div>', unsafe_allow_html=True)
    if st.button("업로드", type="primary", disabled=not up_files):
        saved = 0
        key = dt.date.today().strftime("%Y-%m-%d")
        for uf in up_files:
            try:
                file_id = str(uuid.uuid4())
                safe_name = os.path.splitext(os.path.basename(uf.name))[0]
                store_dir = os.path.join(STORE_DIR, key)
                os.makedirs(store_dir, exist_ok=True)
                store_path = os.path.join(store_dir, f"{file_id}.pdf")
                data = uf.read()
                _save_bytes(store_path, data)
                item = {
                    "id": file_id,
                    "title": safe_name,
                    "original_name": uf.name,
                    "stored_path": store_path,
                    "size": len(data),
                    "notes": "",
                    "created_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
                }
                st.session_state.pdf_index.setdefault(key, []).append(item)
                saved += 1
            except Exception as e:
                st.warning(f"업로드 실패: {uf.name} ({e})")
        if saved:
            save_index(st.session_state.pdf_index)
            st.success(f"{saved}개 파일이 저장되었습니다.")
            st.rerun()

# ------------------------ 액션 유틸 ------------------------
def _save_and_rerun():
    save_index(st.session_state.pdf_index)
    st.rerun()

def delete_item(date_key, item_id):
    lst = st.session_state.pdf_index.get(date_key, [])
    keep = []
    for it in lst:
        if it["id"] == item_id:
            try:
                if os.path.exists(it["stored_path"]):
                    os.remove(it["stored_path"])
            except Exception:
                pass
        else:
            keep.append(it)
    if keep:
        st.session_state.pdf_index[date_key] = keep
    else:
        st.session_state.pdf_index.pop(date_key, None)
    _save_and_rerun()

def set_use(item_id):
    st.session_state.pdf_use = item_id

def read_bytes(path: str, limit_mb: float = 8.0):
    if not os.path.exists(path): return None, 0
    size = os.path.getsize(path)
    if size > limit_mb * 1024 * 1024:
        return None, size
    with open(path, "rb") as f:
        data = f.read()
    return data, size

# ------------------------ 필터링 ------------------------
def matches(it, date_key: str) -> bool:
    if date_key != sel_date_str: return False
    if q:
        qq = q.lower()
        blob = " ".join([it.get("title",""), it.get("notes",""), it.get("original_name","")]).lower()
        if qq not in blob: return False
    return True

filtered = []
for d in sorted(st.session_state.pdf_index.keys(), reverse=True):
    for it in sorted(st.session_state.pdf_index[d], key=lambda x: x.get("updated_at",""), reverse=True):
        if matches(it, d):
            filtered.append((d, it))

# ------------------------ 카드 렌더러 ------------------------
def render_card(date_key: str, it: dict):
    iid = it["id"]
    is_edit = st.session_state.pdf_edit.get(iid, False)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    # 헤더(칩 + 메타) — 즐겨찾기 UI 제거로 2분할
    h1, h2 = st.columns([6,3])
    with h1:
        chips = [f"<span class='pill'>{date_key}</span>",
                 f"<span class='pill src'>PDF</span>",
                 f"<span class='pill'>{human_size(int(it.get('size',0)))}</span>"]
        if st.session_state.pdf_use == iid:
            chips.append("<span class='pill use'>선택됨</span>")
        st.markdown(" ".join(chips), unsafe_allow_html=True)
    with h2:
        st.caption(f"원본: {it.get('original_name','-')}")
        st.caption(f"업데이트: {it.get('updated_at','-')}")

    st.markdown("---")

    if is_edit:
        et_title = st.text_input("제목", value=it.get("title",""), key=f"title-{iid}")
        et_notes = st.text_area("메모", value=it.get("notes",""), key=f"notes-{iid}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("저장", key=f"save-{iid}", type="primary", use_container_width=True):
                it.update({
                    "title": et_title.strip() or it.get("title",""),
                    "notes": et_notes.strip(),
                    "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
                })
                st.session_state.pdf_edit[iid] = False
                _save_and_rerun()
        with c2:
            if st.button("취소", key=f"cancel-{iid}", use_container_width=True):
                st.session_state.pdf_edit[iid] = False
                st.rerun()
    else:
        st.markdown(f"<div class='card-title'>📄 {it.get('title','(제목 없음)')}</div>", unsafe_allow_html=True)
        st.caption(it.get("notes","").strip() or "메모 없음")

        # 액션 버튼들
        a1, a2, a3, a4 = st.columns([1,1,1,1])
        with a1:
            if st.button("✏️ 편집", key=f"edit-{iid}", use_container_width=True):
                st.session_state.pdf_edit[iid] = True
                st.rerun()
        with a2:
            data, size = read_bytes(it.get("stored_path",""))
            if data:
                st.download_button("⬇️ 다운로드", data=data, file_name=it.get("original_name","file.pdf"),
                                   mime="application/pdf", use_container_width=True, key=f"dl-{iid}")
            else:
                st.button("⬇️ 다운로드", disabled=True, use_container_width=True, key=f"dl-{iid}-d")
        with a3:
            st.button("📌 바로 사용", on_click=set_use, args=(iid,), use_container_width=True, key=f"use-{iid}")
        with a4:
            if st.button("🗑 삭제", use_container_width=True, key=f"del-{iid}"):
                delete_item(date_key, iid)

# ------------------------ 출력 ------------------------
st.markdown(f"### {sel_date_str}")
if not filtered:
    st.info("이 날짜에는 PDF가 없습니다. 위의 업로드에서 추가해 보세요.")
else:
    for d, it in filtered:
        render_card(d, it)

# ------------------------ 선택된 PDF 안내 ------------------------
if st.session_state.pdf_use:
    def find_title(iid: str):
        for d, lst in st.session_state.pdf_index.items():
            for it in lst:
                if it["id"] == iid:
                    return it.get("title","")
        return ""
    title = find_title(st.session_state.pdf_use)
    st.success(f"현재 선택된 PDF: {title} — 다른 페이지/기능에서 바로 사용할 수 있어요.")

# 닫기
st.markdown("</div>", unsafe_allow_html=True)
