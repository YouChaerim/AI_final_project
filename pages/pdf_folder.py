# pages/pdf_folder_ui
import streamlit as st
import datetime as dt
import uuid, json, os, tempfile, shutil, base64, requests
from components.auth import require_login
from components.header import render_header
from urllib.parse import urlencode

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"  # 파일에 이미 있다면 그 값 사용
FIXED_USER_ID = "68a57b61743df4d021f534d2"

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

            [data-testid="stAppViewContainer"] > .main .block-container{
  max-width:100% !important;
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

# ========================= API 헬퍼 =========================
def api_list_all():
    r = requests.get(f"{BACKEND_URL}/pdf-folder-api/list",
                     params={"user_id": FIXED_USER_ID}, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def api_list_by_date(date_str: str):
    r = requests.get(f"{BACKEND_URL}/pdf-folder-api/list",
                     params={"user_id": FIXED_USER_ID, "date": date_str}, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def api_upload_one(date_str: str, up_file) -> dict:
    # up_file: Streamlit UploadedFile
    files = {
        "file": (up_file.name, up_file.read(), "application/pdf")
    }
    data = {"user_id": FIXED_USER_ID, "date": date_str}
    r = requests.post(f"{BACKEND_URL}/pdf-folder-api/upload", data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()["item"]

def api_update(pdf_id: str, *, title: str | None = None, notes: str | None = None, date: str | None = None):
    body = {"user_id": FIXED_USER_ID}
    if title is not None:
        body["title"] = title
    if notes is not None:
        body["notes"] = notes
    if date is not None:
        body["date"] = date
    r = requests.put(f"{BACKEND_URL}/pdf-folder-api/update/{pdf_id}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["item"]

def api_delete(pdf_id: str) -> bool:
    r = requests.delete(f"{BACKEND_URL}/pdf-folder-api/delete/{pdf_id}",
                        params={"user_id": FIXED_USER_ID}, timeout=10)
    r.raise_for_status()
    return r.json().get("ok", False)

def api_download_bytes(pdf_id: str) -> bytes:
    r = requests.get(f"{BACKEND_URL}/pdf-folder-api/download/{pdf_id}",
                     params={"user_id": FIXED_USER_ID}, timeout=60)
    r.raise_for_status()
    return r.content

# ========================= 세션 =========================
if "pdf_items" not in st.session_state:
    try:
        st.session_state.pdf_items = api_list_all()
    except Exception as e:
        st.session_state.pdf_items = []
        st.warning(f"PDF 목록을 불러오지 못했어요: {e}")

if "pdf_edit" not in st.session_state:
    st.session_state.pdf_edit = {}
if "pdf_use" not in st.session_state:
    st.session_state.pdf_use = None
if "pdf_q_committed" not in st.session_state:
    st.session_state.pdf_q_committed = ""
if "pdf_sel_date_committed" not in st.session_state:
    st.session_state.pdf_sel_date_committed = None
if "pdf_show_uploader" not in st.session_state:
    st.session_state.pdf_show_uploader = False

def refresh_items():
    st.session_state.pdf_items = api_list_all()

# ========================= 헤더/상단 =========================
render_header()
st.markdown("""
<div class="container">
  <div class="panel-head">PDF 폴더</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='container'>", unsafe_allow_html=True)
btn_left, _ = st.columns([1, 6])
with btn_left:
    st.markdown('<div id="go-folder-left"></div>', unsafe_allow_html=True)
    if st.button("저장폴더로 이동", key="go-folder", type="secondary"):
        try: st.switch_page("pages/folder_page.py")
        except Exception: pass

# ---- 통계칩
items = st.session_state.pdf_items
today_str = dt.date.today().strftime("%Y-%m-%d")
this_week  = dt.date.today().isocalendar().week
cnt_total = len(items)
cnt_today = sum(1 for it in items if it.get("date") == today_str)
def week_of(date_str):
    try:
        y, m, d = map(int, date_str.split("-"))
        return dt.date(y, m, d).isocalendar().week
    except Exception:
        return -1
cnt_week  = sum(1 for it in items if week_of(it.get("date","")) == this_week)

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="statchip">총 파일: {cnt_total}</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="statchip">오늘: {cnt_today}</div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="statchip">이번 주: {cnt_week}</div>', unsafe_allow_html=True)

# ========================= 검색/날짜 =========================
date_keys = sorted({it["date"] for it in items}, reverse=True) if items else []
default_date = st.session_state.pdf_sel_date_committed or (date_keys[0] if date_keys else dt.date.today())
if isinstance(default_date, str):
    default_date = dt.datetime.strptime(default_date, "%Y-%m-%d").date()

with st.form("pdf_search", clear_on_submit=False):
    col_text, col_btn, col_date = st.columns([7, 1.2, 3])
    with col_text:
        st.markdown('<div class="row-label">제목/메모/파일명 검색</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-search-input-anchor"></div>', unsafe_allow_html=True)
        q_input = st.text_input("검색어", placeholder="키워드…", key="pdf_q", label_visibility="collapsed")
    with col_btn:
        st.markdown('<div class="row-label">&nbsp;</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-search-btn-anchor"></div>', unsafe_allow_html=True)
        do_search = st.form_submit_button("검색", use_container_width=True)
    with col_date:
        st.markdown('<div class="row-label">날짜 선택</div>', unsafe_allow_html=True)
        st.markdown('<div id="pdf-date-input-anchor"></div>', unsafe_allow_html=True)
        pick_date = st.date_input("", value=default_date,
                                  format="YYYY-MM-DD", key="pdf_date_input",
                                  label_visibility="collapsed")
    if do_search:
        st.session_state.pdf_q_committed = q_input
        st.session_state.pdf_sel_date_committed = pick_date

q = st.session_state.pdf_q_committed or st.session_state.get("pdf_q", "")
pick_date = st.session_state.pdf_sel_date_committed or st.session_state.get("pdf_date_input", default_date)
sel_date_str = pick_date.strftime("%Y-%m-%d")

st.divider()

# ========================= 업로드 =========================
with st.expander("➕ PDF 추가"):
    top_l, top_r = st.columns([7, 2])
    with top_l:
        st.markdown("<p class='upload-msg'>파일을 선택하고 업로드를 누르면 오늘 날짜로 저장됩니다.</p>", unsafe_allow_html=True)
    with top_r:
        if st.button(("업로더 닫기" if st.session_state.pdf_show_uploader else "파일 선택"),
                     key="toggle-uploader", type="secondary", use_container_width=True):
            st.session_state.pdf_show_uploader = not st.session_state.pdf_show_uploader
            st.rerun()

    up_files = None
    if st.session_state.pdf_show_uploader:
        st.markdown(f"<div id='pdf-upload-wrapper'>", unsafe_allow_html=True)
        up_files = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True,
                                    label_visibility="collapsed", key="pdf_files")
        st.markdown("</div>", unsafe_allow_html=True)

        st.caption("여러 개 선택 가능 · 저장 시 오늘 날짜로 자동 분류됩니다.")
        if st.button("업로드", type="primary", disabled=not up_files, key="do-upload"):
            saved = 0
            today = dt.date.today().strftime("%Y-%m-%d")
            for uf in (up_files or []):
                try:
                    # Streamlit UploadedFile 객체는 .read() 후 포인터가 끝으로 가므로
                    # 각 파일마다 read() 1번만 호출하여 전송합니다.
                    _ = api_upload_one(today, uf)
                    saved += 1
                except Exception as e:
                    st.warning(f"업로드 실패: {uf.name} ({e})")
            if saved:
                refresh_items()
                st.session_state.pdf_show_uploader = False
                st.success(f"{saved}개 파일이 저장되었습니다.")
                st.rerun()

# ========================= 필터링/출력 =========================
def matches(it) -> bool:
    if it.get("date") != sel_date_str:
        return False
    if q:
        qq = q.lower()
        blob = " ".join([
            it.get("title",""),
            it.get("notes",""),
            it.get("original_name","")
        ]).lower()
        return qq in blob
    return True

filtered = [it for it in sorted(items, key=lambda x: x.get("updated_at",""), reverse=True) if matches(it)]

def render_card(it: dict):
    iid = it["id"]; is_edit = st.session_state.pdf_edit.get(iid, False)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if is_edit:
        et_title = st.text_input("제목", value=it.get("title",""), key=f"title-{iid}")
        et_notes = st.text_area("메모", value=it.get("notes",""), key=f"notes-{iid}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("저장", key=f"save-{iid}", type="primary", use_container_width=True):
                try:
                    _ = api_update(iid, title=et_title.strip() or it.get("title",""), notes=et_notes.strip())
                    refresh_items()
                    st.session_state.pdf_edit[iid] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 실패: {e}")
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
            try:
                data = api_download_bytes(iid)
                st.download_button("⬇️ 다운로드", data=data, file_name=it.get("original_name","file.pdf"),
                                   mime="application/pdf", use_container_width=True, key=f"dl-{iid}")
            except Exception:
                st.button("⬇️ 다운로드", disabled=True, use_container_width=True, key=f"dl-{iid}-d")
        with a3:
            if st.button("📌 바로 사용", use_container_width=True, key=f"use-{iid}"):
                st.session_state.pdf_use = iid
                st.rerun()
        with a4:
            if st.button("🗑 삭제", use_container_width=True, key=f"del-{iid}"):
                try:
                    if api_delete(iid):
                        refresh_items()
                        st.rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {e}")

        pv_key = f"pv-{iid}"
        st.session_state.setdefault(pv_key, False)
        if st.button(("🔍 미리보기 닫기" if st.session_state[pv_key] else "🔍 미리보기"),
                     use_container_width=True, key=f"pvbtn-{iid}"):
            st.session_state[pv_key] = not st.session_state[pv_key]; st.rerun()

        if st.session_state[pv_key]:
            try:
                data = api_download_bytes(iid)
                b64 = base64.b64encode(data).decode()
                st.markdown(
                    f"<div class='preview-box'><iframe src='data:application/pdf;base64,{b64}' "
                    f"width='100%' height='640' style='border:0;'></iframe></div>",
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.info(f"미리보기를 불러오지 못했습니다: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

if not filtered:
    st.info("이 날짜에는 PDF가 없습니다. 위의 업로드에서 추가해 보세요.")
else:
    for it in filtered:
        render_card(it)

# 현재 선택된 PDF
if st.session_state.pdf_use:
    def find_title(iid: str):
        for x in st.session_state.pdf_items:
            if x["id"] == iid:
                return x.get("title","")
        return ""
    st.success(f"현재 선택된 PDF: {find_title(st.session_state.pdf_use)} — 다른 페이지/기능에서 바로 사용할 수 있어요.")

st.markdown("</div>", unsafe_allow_html=True)