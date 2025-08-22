# pdf_folder_ui.py
# PDF 폴더 - 날짜별 저장/열람/검색/미리보기/바로사용 (흰 바 완전 제거/토글 업로더/검색 버튼 정렬 유지)
import streamlit as st
import datetime as dt
import uuid, json, os, tempfile, shutil, base64

st.set_page_config(page_title="PDF 폴더", layout="wide", initial_sidebar_state="collapsed")

# ========================= 스타일 =========================
st.markdown("""
<style>
/* 헤더/사이드바/여백 제거 */
html, body { margin:0 !important; padding:0 !important; }
main.stApp{ padding-top:0 !important; }
header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"]{ display:none !important; }
#MainMenu, footer{ visibility:hidden !important; }
section[data-testid="stSidebar"], div[data-testid="stSidebar"],
div[data-testid="stSidebarContent"]{ display:none !important; }
[data-testid="stAppViewContainer"]{ padding-left:0 !important; padding-top:0 !important; }
div[data-testid="block-container"], div[class*="block-container"]{ padding-top:0 !important; padding-bottom:12px !important; }
div[data-testid="block-container"] > div:first-child{ margin-top:0 !important; padding-top:0 !important; }
h1,h2,h3,h4,h5,h6{ margin-top:0 !important; }

/* 컨테이너/타이틀 */
.container{ max-width:1200px; margin:0 auto; padding:0 40px 8px; }
.panel-head{
  margin-top:0; border-radius:18px;
  background:linear-gradient(90deg,#FF9330 0%,#FF7A00 100%);
  color:#fff; font-size:28px; font-weight:900; text-align:center;
  padding:16px 20px; box-shadow:0 8px 18px rgba(0,0,0,.06);
}

/* 통계칩 */
.statbar{display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 8px 0;}
.statchip{
  background:#fff; border-radius:12px; padding:8px 10px;
  box-shadow:0 2px 10px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06);
  font-weight:800; font-size:14px;
}
label{ font-size:0.92rem !important; margin-bottom:2px !important; }

/* 카드 */
.card{
  background:#fff; border-radius:16px; padding:14px 16px;
  box-shadow:0 8px 18px rgba(0,0,0,.06); margin-bottom:10px; border:1px solid rgba(0,0,0,.06);
}
.card-title{font-weight:800; font-size:16px; margin-bottom:6px;}
.card-actions{display:flex; gap:8px; flex-wrap:wrap}
.preview-box{ border:1px solid #eee; border-radius:12px; overflow:hidden; background:#fafafa; }

/* 이동 버튼 */
#go-folder-left + div button{
  background:#fff !important; color:#111 !important;
  border:1px solid rgba(0,0,0,.12) !important; padding:4px 10px !important;
  font-size:14px !important; border-radius:10px !important; box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
}
#go-folder-left + div button:hover{ border-color:rgba(0,0,0,.2) !important; }

/* 검색 줄 크기 일치 */
.row-label{ font-size:0.92rem; font-weight:600; margin:0 0 6px 0; color:#344054; }
:root{ --search-h:44px; --search-r:12px; --search-pad-x:14px; }
#pdf-search-input-anchor + div input,
#pdf-date-input-anchor + div input{
  height:var(--search-h) !important; border-radius:var(--search-r) !important;
  padding:0 var(--search-pad-x) !important; box-sizing:border-box !important;
}
#pdf-search-btn-anchor + div button{
  height:var(--search-h) !important; border-radius:var(--search-r) !important;
  padding:0 var(--search-pad-x) !important; font-weight:800 !important; margin-top:0 !important; width:100% !important;
}
div[data-testid="column"] > div:has(#pdf-search-input-anchor),
div[data-testid="column"] > div:has(#pdf-search-btn-anchor),
div[data-testid="column"] > div:has(#pdf-date-input-anchor){ margin-bottom:0 !important; }

/* ========== 업로더 흰 바 제거 ========== */
/* 1) 기본적으로 업로더는 숨기고(토글로 열기), 열었을 때도 배경/그림자/보더 제거 */
#pdf-upload-wrapper, #pdf-upload-wrapper *{
  background:transparent !important; border:0 !important; box-shadow:none !important;
}
#pdf-upload-wrapper [data-testid="stFileUploaderDropzone"]{
  min-height:0 !important; height:auto !important; padding:0 !important; margin:0 !important; border-radius:0 !important;
  filter:none !important;
}
/* 2) 파일이 선택된 상태에선 드롭존 자체를 완전히 제거 → 흰 바 근원 차단 */
#pdf-upload-wrapper.hide-dropzone [data-testid="stFileUploaderDropzone"]{
  display:none !important;
}
/* 3) 주변 빈 블럭 제거 */
div[data-testid="stVerticalBlock"] > div:has(#pdf-upload-wrapper){
  padding:0 !important; margin:0 !important; background:transparent !important; box-shadow:none !important;
}

/* Expander/Alert 잔여 박스 제거 */
div[data-testid="stExpander"]{ background:transparent !important; border:0 !important; box-shadow:none !important; }
div[data-testid="stExpander"] > details{ background:transparent !important; border:0 !important; box-shadow:none !important; }
div[data-testid="stExpander"] div[role="button"]{ background:transparent !important; border:0 !important; box-shadow:none !important; padding-left:0 !important; padding-right:0 !important; }
div[data-testid="stExpander"] div[role="button"] p{ margin:0 !important; }
div[role="alert"] + div:empty, div[data-testid="stAlert"] + div:empty,
div[role="alert"] + div[data-testid="stVerticalBlock"]:empty,
div[data-testid="stVerticalBlock"]:empty { display:none !important; }

/* 안내 문구 */
.upload-msg{ color:#6b7280; font-weight:700; margin:2px 0 8px; }
</style>
""", unsafe_allow_html=True)

# ========================= 저장 유틸 =========================
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

def load_index() -> dict:
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for d, lst in data.items():
                        for it in lst:
                            it.setdefault("notes", "")
                            it.setdefault("title", it.get("original_name","PDF"))
                    return data
        except Exception:
            pass
    return {}

def save_index(data: dict):
    _atomic_write_json(INDEX_PATH, data)

# ========================= 세션 =========================
if "pdf_index" not in st.session_state: st.session_state.pdf_index = load_index()
if "pdf_edit"  not in st.session_state: st.session_state.pdf_edit  = {}
if "pdf_use"   not in st.session_state: st.session_state.pdf_use   = None
if "pdf_q_committed" not in st.session_state: st.session_state.pdf_q_committed = ""
if "pdf_sel_date_committed" not in st.session_state: st.session_state.pdf_sel_date_committed = None
if "pdf_show_uploader" not in st.session_state: st.session_state.pdf_show_uploader = False  # ← 기본 감춤

idx = st.session_state.pdf_index

# ========================= 헤더 =========================
st.markdown("""
<div class="container">
  <div class="panel-head">PDF 폴더</div>
</div>
""", unsafe_allow_html=True)

# 이동 버튼
st.markdown("<div class='container'>", unsafe_allow_html=True)
btn_left, _ = st.columns([1, 6])
with btn_left:
    st.markdown('<div id="go-folder-left"></div>', unsafe_allow_html=True)
    if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
        try: st.switch_page("pages/folder_page.py")
        except Exception: pass

# 통계칩
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

# ========================= 검색 툴바 =========================
if idx:
    date_keys = sorted([dt.datetime.strptime(k, "%Y-%m-%d").date() for k in idx], reverse=True)
    min_date = min(date_keys); max_date = max(date_keys)
    default_date = st.session_state.pdf_sel_date_committed or date_keys[0]
else:
    date_keys = []; min_date = max_date = default_date = dt.date.today()

with st.form("pdf_search", clear_on_submit=False):
    col_text, col_btn, col_date = st.columns([7, 1.2, 3])

    with col_text:
        st.markdown('<div class="row-label">제목/메모/파일명 검색</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-search-input-anchor"></div>', unsafe_allow_html=True)
        q_input = st.text_input("", placeholder="키워드…", key="pdf_q", label_visibility="collapsed")

    with col_btn:
        st.markdown('<div class="row-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-search-btn-anchor"></div>', unsafe_allow_html=True)
        do_search = st.form_submit_button("검색", use_container_width=True)

    with col_date:
        st.markdown('<div class="row-label">날짜 선택</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-date-input-anchor"></div>', unsafe_allow_html=True)
        pick_date = st.date_input("", value=default_date, min_value=min_date, max_value=max_date,
                                  format="YYYY-MM-DD", key="pdf_date_input", label_visibility="collapsed")

    if do_search:
        st.session_state.pdf_q_committed = q_input
        st.session_state.pdf_sel_date_committed = pick_date

q = st.session_state.pdf_q_committed or st.session_state.get("pdf_q", "")
pick_date = st.session_state.pdf_sel_date_committed or st.session_state.get("pdf_date_input", default_date)
sel_date_str = pick_date.strftime("%Y-%m-%d")

st.divider()

# ========================= 업로드(흰 바 제거 확정) =========================
with st.expander("➕ PDF 추가"):
    top_l, top_r = st.columns([7, 2])
    with top_l:
        st.markdown("<p class='upload-msg'>업로드 된 PDF 파일입니다.!</p>", unsafe_allow_html=True)
    with top_r:
        # 업로더 열고닫기 토글
        if st.button(("업로더 닫기" if st.session_state.pdf_show_uploader else "파일 선택"),
                     key="toggle-uploader", type="secondary", use_container_width=True):
            st.session_state.pdf_show_uploader = not st.session_state.pdf_show_uploader
            st.rerun()

    up_files = None
    if st.session_state.pdf_show_uploader:
        # 파일이 선택되면 드롭존을 display:none 처리하기 위해 클래스 추가
        has_files = bool(st.session_state.get("pdf_files"))
        wrapper_class = "hide-dropzone" if has_files else ""
        st.markdown(f"<div id='pdf-upload-wrapper' class='{wrapper_class}'>", unsafe_allow_html=True)
        up_files = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True,
                                    label_visibility="collapsed", key="pdf_files")
        st.markdown("</div>", unsafe_allow_html=True)

        st.caption("여러 개 선택 가능 · 저장 시 오늘 날짜로 자동 분류됩니다.")
        if st.button("업로드", type="primary", disabled=not up_files, key="do-upload"):
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
                    with open(store_path, "wb") as f: f.write(data)
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
                # 업로드 후 업로더 닫기 → 드롭존/흰 바 재등장 원천 차단
                st.session_state.pdf_show_uploader = False
                st.success(f"{saved}개 파일이 저장되었습니다.")
                st.rerun()

# ========================= 액션 유틸 =========================
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
    if size > limit_mb * 1024 * 1024: return None, size
    with open(path, "rb") as f: data = f.read()
    return data, size

# ========================= 필터링/출력 =========================
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

def render_card(date_key: str, it: dict):
    iid = it["id"]; is_edit = st.session_state.pdf_edit.get(iid, False)
    st.markdown('<div class="card">', unsafe_allow_html=True)

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

        a1, a2, a3, a4 = st.columns([1,1,1,1])
        with a1:
            if st.button("✏️ 편집", key=f"edit-{iid}", use_container_width=True):
                st.session_state.pdf_edit[iid] = True; st.rerun()
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

        pv_key = f"pv-{iid}"; st.session_state.setdefault(pv_key, False)
        if st.button(("🔍 미리보기 닫기" if st.session_state[pv_key] else "🔍 미리보기"),
                     use_container_width=True, key=f"pvbtn-{iid}"):
            st.session_state[pv_key] = not st.session_state[pv_key]; st.rerun()

        if st.session_state[pv_key]:
            data, size = read_bytes(it.get("stored_path",""))
            if data:
                b64 = base64.b64encode(data).decode()
                st.markdown(
                    f"<div class='preview-box'><iframe src='data:application/pdf;base64,{b64}' "
                    f"width='100%' height='640' style='border:0;'></iframe></div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("파일이 큽니다. 다운로드로 열어 주세요.")

    st.markdown("</div>", unsafe_allow_html=True)

if not filtered:
    st.info("이 날짜에는 PDF가 없습니다. 위의 업로드에서 추가해 보세요.")
else:
    for d, it in filtered: render_card(d, it)

# 선택된 PDF 안내
if st.session_state.pdf_use:
    def find_title(iid: str):
        for d, lst in st.session_state.pdf_index.items():
            for it in lst:
                if it["id"] == iid: return it.get("title","")
        return ""
    st.success(f"현재 선택된 PDF: {find_title(st.session_state.pdf_use)} — 다른 페이지/기능에서 바로 사용할 수 있어요.")

st.markdown("</div>", unsafe_allow_html=True)
