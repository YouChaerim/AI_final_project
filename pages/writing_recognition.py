# app.py
# -*- coding: utf-8 -*- (유니코드로 수정 2025/07/25)
import io, os, re, gc, json, random, base64
import numpy as np
import streamlit as st
import cv2
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError

# =========================
# 환경변수 로드 (.env)
# =========================
load_dotenv(dotenv_path="C:/Users/user/Desktop/main_project/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POPPLER_PATH   = os.getenv("POPPLER_PATH")  # 예) C:/Users/user/anaconda3/envs/final/Library/bin

# =========================
# 페이지 기본 설정
# =========================
st.set_page_config(page_title="📄 OCR + GPT 요약/퀴즈 생성기",
                   layout="wide",
                   initial_sidebar_state="collapsed")

# =========================
# (추가) 캐릭터 이미지 유틸 — folder_page와 동일
# =========================
def _resolve_assets_root():
    here = os.path.dirname(__file__)
    cands = [
        os.path.abspath(os.path.join(here, "assets")),
        os.path.abspath(os.path.join(here, "..", "assets")),
    ]
    for p in cands:
        if os.path.isdir(p):
            return p
    return cands[0]

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def get_char_image_uri(char_key: str) -> str:
    p = os.path.join(ASSETS_ROOT, "characters", f"{char_key}.png")
    if os.path.exists(p):
        return _to_data_uri(p)
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

# ---- THEME (folder_page와 동일 팔레트)
u = st.session_state.get("user_data") or {}
dark = bool(u.get("dark_mode", False))

if dark:
    bg = "#1C1C1E"; fg = "#F2F2F2"; nav_bg = "#2C2C2E"
    panel_bg = "#1F1F22"; panel_shadow = "rgba(0,0,0,.35)"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"; nav_bg = "rgba(255,255,255,.9)"
    panel_bg = "#FFFFFF"; panel_shadow = "rgba(0,0,0,.08)"

# =========================
# 스타일 (folder_page의 헤더/패널 그대로 복제 + 하얀 바 제거)
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg}; }}
.block-container {{ padding-top:0 !important; }}
header {{ display:none !important; }}

/* 본문 컨테이너: folder_page와 동일 (상단 4px, 좌우 40px) */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}

/* 헤더 — folder_page와 동일 */
a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background:{nav_bg};
  box-shadow:0 2px 4px rgba(0,0,0,.05);
}}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:900; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:700; }}
.nav-menu div a {{ color:#000 !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{
  width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.06);
}}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; }}

/* 패널 — folder_page와 100% 동일 */
.panel {{
  position: relative;
  background:{panel_bg};
  border-radius:18px;
  box-shadow:0 6px 24px {panel_shadow};
  overflow:hidden;
  margin-top:0px;
}}
/* 주황 헤더 */
.panel-head {{
  background: linear-gradient(90deg,#FF9330,#FF7A00);
  color:white; text-align:center; font-size:34px; font-weight:900; padding:18px 20px;
}}
/* 하얀 패널-바 완전히 제거 (두 탭 페이지 공통) */
.panel-body {{ display:none !important; height:0 !important; padding:0 !important; border:0 !important; }}

/* 탭을 주황 박스 '바로 아래'로 */
.stTabs {{ margin-top:12px !important; }}
.stTabs [role="tablist"] {{ gap: 14px; }}
.stTabs [role="tab"] {{ font-weight:800; }}
.stTabs [role="tab"][aria-selected="true"] {{ color:#FF7A30 !important; }}

/* 기존 카드/버튼 스킨 유지 */
.capture-card {{ width:100%; background:#fff; border:1px solid #F1E6D8; border-radius:18px;
  box-shadow:0 18px 48px rgba(17,24,39,.06); padding:22px 22px 18px; margin-top:16px; }}
.cam-square {{ width:340px; height:340px; border-radius:18px; background:linear-gradient(180deg,#F6F9FF 0%,#EEF2F7 100%);
  border:1px solid #E9EEF6; box-shadow:0 1px 0 #FFFFFF inset, 0 10px 26px rgba(17,24,39,.06); display:flex; align-items:center; justify-content:center; }}
.cam-square .inner{{ display:flex; flex-direction:column; align-items:center; gap:16px; color:#8A94A6; }}
.cam-square .label{{ font-weight:800; font-size:18px; color:#6B7280; }}
.right-col .title {{ font-size:44px; font-weight:900; margin:2px 0 6px; }}
.right-col .desc  {{ font-size:20px; color:#4B5563; margin-bottom:12px; }}
.btn-row {{ display:flex; gap:12px; align-items:center; margin:2px 0 6px; }}
.btn-row > .cell {{ flex:1; }}
div[data-testid="stFileUploader"]{{ width:100%; }}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]{{
  padding:0 !important; border:none !important; height:52px; border-radius:12px;
  background:linear-gradient(90deg,#FF8A00,#FF7A00); box-shadow:0 8px 18px rgba(255,138,0,.18); cursor:pointer;
}}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] * ,
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"] * {{ display:none !important; }}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::after,
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]::after{{
  content:"파일 업로드"; display:flex; align-items:center; justify-content:center;
  height:52px; width:100%; color:#fff; font-weight:900; letter-spacing:.2px;
}}
div[data-testid="stFileUploader"] label {{ display:none !important; }}
.primary-btn .stButton>button{{ height:52px; width:100%; padding:0 22px; background:linear-gradient(90deg,#FF8A00,#FF7A00);
  color:#fff; border:0; border-radius:12px; font-weight:900; box-shadow:0 8px 18px rgba(255,138,0,.18); }}
.primary-btn .stButton>button:disabled{{ opacity:.45; cursor:not-allowed; }}
.ghost-btn .stButton>button{{ height:52px; width:100%; border-radius:12px; border:1.5px solid #E5E7EB; background:#fff; font-weight:800; }}

.quiz-shell{{ width:100%; background:#fff; border:2px solid #FFA65A; border-radius:10px; box-shadow:0 8px 24px rgba(17,24,39,.08); overflow:hidden; }}
.quiz-header{{ background:linear-gradient(90deg,#FF7A00,#FFA74D); color:#fff; text-align:center; font-weight:900; font-size:36px; padding:14px 0; border-bottom:1px solid #EFD0B2; }}
.quiz-body{{ padding:22px 24px 26px; }}
.opt2 .stButton>button{{ width:100%; border:1.5px solid #EFEFEF; background:#fff; border-radius:12px; padding:14px 16px; text-align:left; font-weight:700; box-shadow:0 1px 2px rgba(0,0,0,0.03); }}
.opt2 .stButton>button:hover{{ border-color:#FFD2A8; }}
.opt2.selected .stButton>button{{ border-color:#FFB066; box-shadow:0 0 0 2px rgba(255,138,0,.15) inset; }}

/* 빈 블럭 제거 */
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
</style>
""", unsafe_allow_html=True)

# =========================
# OpenAI 클라이언트
# =========================
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키(OPENAI_API_KEY)를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()
MODEL_SUMMARY = "gpt-4o-mini"

# =========================
# OCR (PaddleOCR)
# =========================
@st.cache_resource
def get_ocr():
    from paddleocr import PaddleOCR
    for kwargs in [
        dict(lang="korean", use_angle_cls=True),
        dict(lang="korean"),
        dict(),
    ]:
        try:
            return PaddleOCR(**kwargs)
        except TypeError:
            continue
    st.error("❌ PaddleOCR 초기화 실패: 버전 호환 문제가 있습니다.")
    st.stop()

# =========================
# 유틸
# =========================
def _prep_im_for_ocr(pil_img: Image.Image, max_side: int = 2000) -> np.ndarray:
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    arr = np.array(pil_img)
    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    h, w = arr.shape[:2]
    m = max(h, w)
    if m > max_side:
        scale = max_side / float(m)
        arr = cv2.resize(arr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
    return np.ascontiguousarray(arr)

def _group_runs(pages):
    if not pages: return []
    runs, s, e = [], pages[0], pages[0]
    for p in pages[1:]:
        if p == e + 1:
            e = p
        else:
            runs.append((s, e))
            s = e = p
    runs.append((s, e))
    return runs

@st.cache_data(show_spinner=False)
def pdf_pages_to_texts(pdf_bytes: bytes, *, dpi: int = 120, min_chars_for_pdftext: int = 10):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        base_pages = [(i+1, (p.extract_text() or "")) for i, p in enumerate(reader.pages)]
    except Exception:
        base_pages = []
    total_pages = len(base_pages)

    if total_pages == 0:
        try:
            kw = {"dpi": dpi}
            if POPPLER_PATH: kw["poppler_path"] = POPPLER_PATH
            images = convert_from_bytes(pdf_bytes, **kw)
        except PDFInfoNotInstalledError:
            st.warning("⚠️ Poppler 미설치: OCR 사용 불가")
            return [], 0
        ocr = get_ocr()
        out, prog = [], st.progress(0.0, text=f"OCR 전체 진행 중… ({len(images)}p, DPI={dpi})")
        for i, img in enumerate(images, start=1):
            arr = _prep_im_for_ocr(img, max_side=2000)
            res = ocr.ocr(arr)
            txt = "\n".join("".join([w[0] for w in line]) for line in (res[0] or [])) if res else ""
            out.append((i, txt))
            prog.progress(i/len(images))
            del img
        prog.empty()
        return out, len(images)

    lengths = [len((t or "").strip()) for _, t in base_pages]
    text_pages = sum(1 for L in lengths if L >= min_chars_for_pdftext)
    coverage = text_pages / max(1, total_pages)

    if coverage >= 0.70:
        return base_pages, total_pages

    if coverage < 0.30:
        try:
            kw = {"dpi": dpi}
            if POPPLER_PATH: kw["poppler_path"] = POPPLER_PATH
            images = convert_from_bytes(pdf_bytes, **kw)
        except PDFInfoNotInstalledError:
            return base_pages, total_pages
        ocr = get_ocr()
        out, prog = [], st.progress(0.0, text=f"OCR 전체 진행 중… ({len(images)}p, DPI={dpi})")
        for i, img in enumerate(images, start=1):
            arr = _prep_im_for_ocr(img, max_side=2000)
            res = ocr.ocr(arr)
            txt = "\n".join("".join([w[0] for w in line]) for line in (res[0] or [])) if res else ""
            out.append((i, txt))
            prog.progress(i/len(images))
        prog.empty()
        return out, len(images)

    need_pages = [pg for (pg, t) in base_pages if len((t or "").strip()) < min_chars_for_pdftext]
    runs = _group_runs(need_pages)
    page_to_text = {pg: (t or "") for pg, t in base_pages}
    ocr = get_ocr()
    done = 0
    prog = st.progress(0.0, text=f"하이브리드: 부족 페이지만 OCR 중… (총 {len(need_pages)}p, DPI={dpi})")
    for s, e in runs:
        try:
            kw = {"dpi": dpi, "first_page": s, "last_page": e}
            if POPPLER_PATH: kw["poppler_path"] = POPPLER_PATH
            imgs = convert_from_bytes(pdf_bytes, **kw)
        except PDFInfoNotInstalledError:
            break
        for idx, pg in enumerate(range(s, e+1)):
            arr = _prep_im_for_ocr(imgs[idx], max_side=2000)
            res = ocr.ocr(arr)
            t2 = "\n".join("".join([w[0] for w in line]) for line in (res[0] or [])) if res else ""
            page_to_text[pg] = t2
            done += 1
            prog.progress(done / max(1, len(need_pages)))
    prog.empty()
    out = [(pg, page_to_text.get(pg, "")) for pg, _ in base_pages]
    return out, total_pages

# =========================
# 요약/퀴즈 유틸 (기존 유지)
# =========================
def split_text_by_chars(s: str, max_chars: int):
    paras = re.split(r"\n{2,}", s)
    chunks, buff = [], ""
    for p in paras:
        p = p.strip()
        if not p: continue
        if len(buff) + len(p) + 2 <= max_chars:
            buff = (buff + "\n\n" + p).strip()
        else:
            if buff: chunks.append(buff)
            if len(p) > max_chars:
                sents = re.split(r"(?<=[.!?。！？])\s+", p)
                cur = ""
                for sent in sents:
                    if len(cur) + len(sent) + 1 <= max_chars:
                        cur = (cur + " " + sent).strip()
                    else:
                        if cur: chunks.append(cur)
                        cur = sent
                if cur: chunks.append(cur)
            else:
                buff = p
    if buff: chunks.append(buff)
    return chunks

def gpt_chat(messages, model=MODEL_SUMMARY, temperature=0.2, max_tokens=None):
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def target_lines_for_length(n_chars: int) -> int:
    if n_chars < 1500: return 4
    elif n_chars < 5000: return 6
    elif n_chars < 12000: return 8
    elif n_chars < 25000: return 10
    elif n_chars < 50000: return 13
    else: return 16

def summarize_large_text(text, target_lines=8, base_chunk_chars=7000, reduce_chunk_chars=4000):
    if not text or len(text.strip()) == 0: return ""
    chunks = split_text_by_chars(text, base_chunk_chars)
    part_summaries = []
    if len(chunks) == 1:
        sys = f"아래 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로 핵심만 간결하게 요약해줘."
        return gpt_chat(
            [{"role": "system", "content": sys},
             {"role": "user", "content": chunks[0]}]
        )
    prog = st.progress(0.0, text="1/3 단계: 부분 요약 중...")
    for i, ck in enumerate(chunks, start=1):
        sys = "아래 텍스트의 핵심 논지/키워드/숫자만 5~7문장으로 요약."
        ps = gpt_chat([{"role":"system","content":sys},{"role":"user","content":ck}])
        part_summaries.append(ps); prog.progress(i/len(chunks))
    combined = "\n\n".join(part_summaries)
    reduce_chunks = split_text_by_chars(combined, reduce_chunk_chars)
    reduce_summaries = []
    prog = st.progress(0.0, text="2/3 단계: 요약 통합 중...")
    for i, rc in enumerate(reduce_chunks, start=1):
        sys2 = "아래 요약들을 중복 제거하고 핵심만 압축해 4~6문장으로 재요약."
        rs = gpt_chat([{"role":"system","content":sys2},{"role":"user","content":rc}])
        reduce_summaries.append(rs); prog.progress(i/len(reduce_chunks))
    final_source = "\n\n".join(reduce_summaries)
    sys3 = f"전체 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로, 숫자/고유명사 유지하며 최종 요약."
    prog = st.progress(0.0, text="3/3 단계: 최종 요약 정리 중...")
    final = gpt_chat([{"role":"system","content":sys3},{"role":"user","content":final_source}])
    prog.progress(1.0); return final

def summarize_content(content: str):
    if not content or not content.strip(): return "요약할 내용이 없습니다."
    n = len(content); target_lines = target_lines_for_length(n)
    st.info(f"📏 문서 길이: 약 {n:,}자 → 목표 요약: **{target_lines}줄**")
    if n <= 5000:
        try:
            sys = f"아래 내용을 {max(2, target_lines-1)}~{target_lines+1}줄로 핵심만 요약해줘."
            return gpt_chat([{"role":"system","content":sys},{"role":"user","content":content}])
        except Exception:
            return summarize_large_text(content, target_lines=target_lines)
    else:
        return summarize_large_text(content, target_lines=target_lines)

def _safe_json_parse(s: str):
    s = s.strip()
    m = re.search(r"\[.*\]", s, flags=re.S)
    if m: s = m.group(0)
    try:
        import json5
        return json5.loads(s)
    except Exception:
        return json.loads(s)

def generate_quiz(content: str, count: int = 8, allowed_types: set = None):
    if not content.strip(): return []
    if not allowed_types:
        allowed_types = {"객관식","OX","단답형"}

    system = "너는 한국어 학습용 퀴즈 출제 도우미야. 항상 JSON만 출력해."
    user = f"""
다음 학습 내용을 바탕으로 퀴즈 {count}문제를 생성해.
허용 유형: {sorted(list(allowed_types))}
- 각 문제: {{"type":"객관식|OX|단답형","question":"문제","options":["보기1",...],"answer":"정답 또는 [정답들]","explanation":"간단 해설"}}
- 객관식 ≥ 4지선다, OX는 ["O","X"] 고정, 단답형은 options 빈 리스트 허용.
- JSON 배열만 출력.
내용:
\"\"\"{content[:20000]}\"\"\""""
    try:
        raw = gpt_chat(
            [{"role":"system","content":system},{"role":"user","content":user}],
            model=MODEL_SUMMARY, temperature=0.2, max_tokens=2000
        )
        data = _safe_json_parse(raw)
        if not isinstance(data, list): return []
        norm = []
        for item in data:
            qtype = (item.get("type","") or "").strip()
            if qtype not in {"객관식","OX","단답형"}: continue
            q = {
                "type": qtype,
                "question": item.get("question","").strip(),
                "options": item.get("options", []) or ([] if qtype=="단답형" else (["O","X"] if qtype=="OX" else [])),
                "answer": item.get("answer", ""),
                "explanation": item.get("explanation", "")
            }
            if qtype == "OX": q["options"] = ["O","X"]
            norm.append(q)
        if len(norm) > count: norm = norm[:count]
        return norm
    except Exception:
        return []

def ask_gpt_about_wrong(qobj: dict, user_answer: str) -> str:
    question = qobj.get("question","")
    answer   = qobj.get("answer","")
    expl     = qobj.get("explanation","")
    opts     = qobj.get("options", [])
    system = "너는 한국어 교사야. 학생의 오답을 짧고 명확히 설명해."
    user = f"""문제: {question}
선택지: {opts}
학생의 답: {user_answer}
정답: {answer}
기존 해설: {expl}
요청: 3~5문장 설명 + 핵심 키워드 1~2개."""
    try:
        return gpt_chat([{"role":"system","content":system},{"role":"user","content":user}], model=MODEL_SUMMARY, temperature=0.2, max_tokens=500)
    except Exception:
        return expl or "해설 생성에 실패했습니다."

# =========================
# 공통 헤더 (folder_page와 동일) — 캐릭터 이미지 적용
# =========================
char_key = (st.session_state.get("user_data") or {}).get("active_char", "rabbit")
header_avatar_uri = get_char_image_uri(char_key)

st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/"             target="_self">메인페이지</a></div>
      <div><a href="/main"         target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle"   target="_self">PDF 요약</a></div>
      <div><a href="/folder_page"  target="_self">저장폴더</a></div>
      <div><a href="/quiz"         target="_self">퀴즈</a></div>
      <div><a href="/report"       target="_self">리포트</a></div>
      <div><a href="/ranking"      target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터"><img src="{header_avatar_uri}" alt="avatar"/></div>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# 본문 컨테이너
# =========================
st.markdown('<div class="container">', unsafe_allow_html=True)

# 🔶 저장폴더 스타일과 동일한 주황 패널 (하얀 바 제거)
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-head">PDF 요약</div>', unsafe_allow_html=True)
st.markdown('<div class="panel-body"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 그 '아래'에 탭 배치
tab1, tab2 = st.tabs(["📄 PDF 요약", "🧠 퀴즈 생성기"])

# -------------------------------------------------------------------
# TAB 1: PDF 요약
# -------------------------------------------------------------------
with tab1:
    st.markdown('<div class="capture-card">', unsafe_allow_html=True)
    left, right = st.columns([1,2], gap="large")
    with left:
        st.markdown("""
        <div class="cam-square">
          <div class="inner">
            <svg width="86" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 7h3l1-2h8l1 2h3a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" stroke="#93A3B8" stroke-width="1.5"/>
              <circle cx="12" cy="13" r="4" stroke="#93A3B8" stroke-width="1.5"/>
            </svg>
            <div class="label">촬영화면</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown('<div class="right-col"><div class="title">PDF 인식</div><div class="desc">PDF 내용을 텍스트로 변환합니다.</div>', unsafe_allow_html=True)
        c_up, c_go = st.columns([2,1], gap="small")
        with c_up:
            st.markdown('<div class="btn-row"><div class="cell">', unsafe_allow_html=True)
            uploaded = st.file_uploader("PDF 파일 업로드", type=["pdf"], key="pdf_uploader_main")
            st.markdown('</div></div>', unsafe_allow_html=True)
        with c_go:
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            quick_go = st.button("요약하기", use_container_width=True, key="quick_summary_btn")
            st.markdown('</div>', unsafe_allow_html=True)
        st.caption("PDF를 업로드하면 요약 가능합니다.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 기능 로직 (기존과 동일)
    if 'uploaded' not in locals() or not uploaded:
        st.info("PDF를 업로드하면 **페이지별 텍스트 확보** → (필요시) **벡터DB 인덱싱** → 원하는 **페이지 범위만 RAG 요약**할 수 있어요.")
        pages_text, total_pages, pdf_bytes, have_rag, doc_id = [], 0, None, False, None
    else:
        pdf_bytes = uploaded.read()
        have_rag = True
        try:
            from lib.rag_utils import (upsert_doc, doc_exists, _sha1_bytes, rag_summarize_section, format_context)
        except Exception:
            have_rag = False
            st.warning("⚠️ RAG 모듈(lib/rag_utils.py)을 찾지 못했습니다. '일반 요약'만 사용 가능합니다.")
        doc_id = None
        total_pages = 0
        pages_text = []
        if have_rag:
            doc_id_guess = _sha1_bytes(pdf_bytes)
            if doc_exists(doc_id_guess):
                doc_id = doc_id_guess
                try:
                    total_pages = len(PdfReader(io.BytesIO(pdf_bytes)).pages)
                except Exception:
                    total_pages = 1
            else:
                with st.spinner("PDF 페이지 텍스트 확보 중…"):
                    pages_text, total_pages = pdf_pages_to_texts(pdf_bytes, dpi=120, min_chars_for_pdftext=10)
                if total_pages == 0:
                    st.error("PDF에서 페이지를 찾지 못했습니다."); st.stop()
                with st.spinner("벡터DB 인덱싱 중… (재인덱싱 방지)"):
                    added, doc_id = upsert_doc(pages_text, source_name=uploaded.name, file_bytes=pdf_bytes,
                                               chunk_size=800, overlap=200, force=False)
                st.success(f"📦 인덱싱 상태 — 페이지 {total_pages} / 신규 청크 {added}개 (doc_id: {doc_id})")
        else:
            with st.spinner("PDF 페이지 텍스트 확보 중…"):
                pages_text, total_pages = pdf_pages_to_texts(pdf_bytes, dpi=120, min_chars_for_pdftext=10)
            if total_pages == 0:
                st.error("PDF에서 페이지를 찾지 못했습니다."); st.stop()

    if 'quick_go' in locals() and quick_go:
        if not uploaded:
            st.warning("먼저 PDF를 업로드해주세요.")
        else:
            if not pages_text:
                pages_text, _ = pdf_pages_to_texts(pdf_bytes, dpi=120, min_chars_for_pdftext=10)
            all_text = "\n\n".join([t for _, t in pages_text])
            res = summarize_content(all_text)
            st.markdown("### 🧾 전체 요약 (빠른)")
            st.write(res)
            st.session_state["summary"] = res

    if 'uploaded' in locals() and uploaded:
        st.markdown("---")
        st.subheader("📌 요약 구간 선택")
        if total_pages > 1:
            page_s, page_e = st.slider("페이지 범위", 1, total_pages, (1, min(5, total_pages)))
        else:
            page_s, page_e = 1, 1
            st.caption("문서가 1페이지입니다.")
        query = st.text_input("요약 주제/질문(선택, 공백이면 '핵심 요약')", value="핵심 요약")

        c1, c2 = st.columns(2)
        with c1:
            if have_rag and st.button("📝 선택 구간만 RAG 요약", use_container_width=True):
                with st.spinner("선택 구간 컨텍스트 검색 및 요약 중…"):
                    out = rag_summarize_section(client=client, model=MODEL_SUMMARY, doc_id=doc_id,
                                                query=query or "핵심 요약",
                                                page_range=(page_s, page_e),
                                                max_chars_context=9000, top_k=16)
                st.markdown("### ✅ 요약 결과 (선택 구간/RAG)")
                st.write(out["summary"])
                st.session_state["summary"] = out["summary"]
                from lib.rag_utils import format_context
                with st.expander("🔎 근거 컨텍스트 보기"):
                    st.code(format_context(out["evidence"]))

        with c2:
            if st.button("📄 전체 문서 일반 요약", use_container_width=True):
                if not pages_text:
                    pages_text, _ = pdf_pages_to_texts(pdf_bytes, dpi=120, min_chars_for_pdftext=10)
                all_text = "\n\n".join([t for _, t in pages_text])
                res = summarize_content(all_text)
                st.markdown("### 🧾 전체 요약 (일반)")
                st.write(res)
                st.session_state["summary"] = res

            if have_rag and st.button("🧠 전체 문서 RAG 요약(근거)", use_container_width=True):
                with st.spinner("전체 문서 컨텍스트 검색(RAG) 및 요약 중…"):
                    out = rag_summarize_section(client=client, model=MODEL_SUMMARY, doc_id=doc_id,
                                                query=(query or "전체 핵심 요약"),
                                                page_range=(1, total_pages),
                                                max_chars_context=9000, top_k=16)
                st.markdown("### ✅ 전체 문서 RAG 요약 (근거 포함)")
                st.write(out["summary"])
                st.session_state["summary"] = out["summary"]
                from lib.rag_utils import format_context
                with st.expander("🔎 근거 컨텍스트 보기"):
                    st.code(format_context(out["evidence"]))

    st.caption("💡 요약 결과는 자동으로 퀴즈 탭에 전달됩니다.")

# -------------------------------------------------------------------
# TAB 2: 퀴즈 생성기
# -------------------------------------------------------------------
with tab2:
    if "quiz_stage" not in st.session_state:
        st.session_state.quiz_stage = "setup"

    if st.session_state.quiz_stage == "setup":
        st.markdown('<div class="capture-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,2,2], gap="large")
        with c1:
            quiz_count = st.number_input("문항 수", min_value=4, max_value=20, value=8, step=1, key="count_input")
            shuffle = st.checkbox("선택지 섞기", value=True, key="shuffle_input")
        with c2:
            st.markdown("**유형 선택**")
            t_obj = st.checkbox("객관식", value=True, key="t_obj")
            t_ox  = st.checkbox("OX", value=True, key="t_ox")
            t_sa  = st.checkbox("단답형", value=True, key="t_sa")
            allowed_types = [t for t, ok in [("객관식", t_obj), ("OX", t_ox), ("단답형", t_sa)] if ok]
        with c3:
            content_default = st.session_state.get("summary", "")
            content_input = st.text_area("✍️ 학습 내용을 입력하거나 PDF 요약 결과를 사용하세요",
                                         value=content_default,
                                         height=120, key="quiz_content_input")
            st.caption("✅ PDF 요약 결과가 있으면 자동으로 채워집니다.")
        if st.button("🧠 퀴즈 생성하기", key="make_quiz"):
            content_to_use = (st.session_state.get("quiz_content_input","") or "").strip()
            if not content_to_use:
                st.warning("내용을 입력하거나 요약 결과를 생성해주세요.")
            else:
                with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                    st.session_state.summary_log = summarize_content(content_to_use)
                    data = generate_quiz(content_to_use, st.session_state.count_input, allowed_types=set(allowed_types))
                    if not data:
                        st.error("퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                    else:
                        if st.session_state.shuffle_input:
                            for q in data:
                                if (q.get("type") in ["객관식","OX"]) and isinstance(q.get("options"), list):
                                    random.shuffle(q["options"])
                        st.session_state.quiz_data = data
                        st.session_state.user_answers = {}
                        st.session_state.current_idx = 0
                        st.session_state.graded = False
                        st.session_state.score = 0
                        st.session_state.quiz_stage = "play"
                        st.rerun()
        if st.session_state.get("summary_log"):
            st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.quiz_stage == "play":
        if not st.session_state.get("quiz_data"):
            st.session_state.quiz_stage = "setup"
            st.rerun()

        back_col, _ = st.columns([1,5])
        with back_col:
            if st.button("← 다시 생성", key="back_setup"):
                for k in ["quiz_data","user_answers","current_idx","graded","score","summary_log"]:
                    if k in st.session_state: del st.session_state[k]
                st.session_state.quiz_stage = "setup"
                st.rerun()

        def _normalize(s):
            if isinstance(s, (list, tuple)): return [str(x).strip().lower() for x in s]
            return str(s).strip().lower()
        def _is_correct(user, answer):
            u_ = _normalize(user); a_ = _normalize(answer)
            if isinstance(a_, list): return u_ in a_
            return u_ == a_

        def _render_player():
            qlist = st.session_state.quiz_data
            idx = st.session_state.current_idx
            total = len(qlist)
            q = qlist[idx]
            qtype = (q.get("type","") or "").strip()

            st.markdown('<div class="quiz-shell">', unsafe_allow_html=True)
            st.markdown('<div class="quiz-header">퀴즈 풀기</div>', unsafe_allow_html=True)
            st.markdown('<div class="quiz-body">', unsafe_allow_html=True)

            st.markdown(f'<div class="quiz-meta">{idx+1}/{total}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quiz-question">{q.get("question","-")}</div>', unsafe_allow_html=True)

            if qtype in ["객관식","OX"]:
                options = q.get("options", []) or (["O","X"] if qtype=="OX" else [])
                letters = ["A","B","C","D","E","F"]
                if idx not in st.session_state.user_answers:
                    st.session_state.user_answers[idx] = None

                def tile(opt_text, letter, k, selected):
                    st.markdown(f"<div class='opt2{' selected' if selected else ''}'>", unsafe_allow_html=True)
                    clicked = st.button(f"{letter}  {opt_text}", key=k, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    return clicked

                for r in range(0, len(options), 2):
                    g1, g2 = st.columns(2, gap="small")
                    with g1:
                        if r < len(options):
                            opt = options[r]
                            sel = (st.session_state.user_answers[idx] == opt)
                            if tile(opt, letters[r], f"nopt_{idx}_{r}", sel):
                                st.session_state.user_answers[idx] = opt
                    with g2:
                        if r+1 < len(options):
                            opt = options[r+1]
                            sel = (st.session_state.user_answers[idx] == opt)
                            if tile(opt, letters[r+1], f"nopt_{idx}_{r+1}", sel):
                                st.session_state.user_answers[idx] = opt
            else:
                key = f"sa_{idx}"
                val = st.text_input("정답을 입력하세요", key=key)
                st.session_state.user_answers[idx] = val

            st.markdown('<div class="action-row">', unsafe_allow_html=True)
            cprev, cnext = st.columns([1,1], gap="small")
            with cprev:
                if st.button("이전", key=f"prev_{idx}") and st.session_state.current_idx > 0:
                    st.session_state.current_idx -= 1
            with cnext:
                if idx < total-1:
                    if st.button("다음", key=f"next_{idx}"):
                        st.session_state.current_idx += 1
                else:
                    if st.button("제출/채점", key="submit_all"):
                        score = 0
                        for i, qq in enumerate(qlist):
                            user = st.session_state.user_answers.get(i, "")
                            if _is_correct(user, qq.get("answer","")):
                                score += 1
                        st.session_state.score = score
                        st.session_state.graded = True
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        _render_player()

        if st.session_state.get("graded"):
            total = len(st.session_state.quiz_data)
            score = st.session_state.get("score", 0)
            st.markdown(f"<span class='score-pill'>점수: {score} / {total}</span>", unsafe_allow_html=True)
            ratio = score/total if total else 0
            st.markdown('🎉 <span class="result-good">잘했어요!</span>' if ratio >= 0.6 
                        else '💪 <span class="result-bad">조금만 더!</span>', unsafe_allow_html=True)

            wrongs = []
            for i, q in enumerate(st.session_state.quiz_data):
                user = st.session_state.user_answers.get(i, "")
                if not _is_correct(user, q.get("answer","")):
                    wrongs.append((i, q, user))
            if wrongs:
                st.markdown("---")
                st.markdown("#### 오답 해설")
                for i, q in wrongs:
                    with st.expander(f"문제 {i+1} - 내 답: {user} / 정답: {q.get('answer','')}", expanded=False):
                        try:
                            why = ask_gpt_about_wrong(q, user)
                        except Exception:
                            why = q.get("explanation","")
                        st.write(why)

# =========================
# 하단 전체 새로고침
# =========================
st.markdown("<hr style='border:none; border-top:1px dashed rgba(0,0,0,.08); margin: 16px 0 8px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
if st.button("🔄 전체 새로고침", key="refresh_all"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# 컨테이너 닫기
st.markdown("</div>", unsafe_allow_html=True)
