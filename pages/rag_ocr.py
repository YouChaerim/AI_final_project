# app.py
# -*- coding: utf-8 -*- (유니코드로 수정 2025/07/25)
import io, os, re, gc
import numpy as np
import streamlit as st
import cv2
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError

# ===== ✅ .env에서 환경변수 불러오기 =====
load_dotenv(dotenv_path="C:/Users/user/Desktop/main_project/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POPPLER_PATH   = os.getenv("POPPLER_PATH")  # 선택: pdf2image 경로 지정(poppler)
# 예) POPPLER_PATH=C:/Users/user/anaconda3/envs/final/Library/bin

# ===== 페이지 기본 설정 =====
st.set_page_config(page_title="📄 OCR + GPT 요약/퀴즈 생성기",
                   layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown("""
<style>
[data-testid="stSidebar"]{display:none!important;}
.stTextArea textarea{font-size:.95rem;line-height:1.5;}
.stAlert{margin-top:.5rem;}
</style>
""", unsafe_allow_html=True)

# ===== ✅ OpenAI 클라이언트 캐싱 =====
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()
MODEL_SUMMARY = "gpt-4o-mini"   # 필요 시 교체

# ===== ✅ PaddleOCR 캐싱 (호환형) =====
# ===== ✅ PaddleOCR 캐싱 (호환형) =====
@st.cache_resource
def get_ocr():
    from paddleocr import PaddleOCR
    # 가장 보수적으로: 지원 가능성이 높은 인자부터 시도
    for kwargs in [
        dict(lang="korean", use_angle_cls=True),
        dict(lang="korean"),
        dict(),  # 최후의 수단: 완전 기본값
    ]:
        try:
            return PaddleOCR(**kwargs)
        except TypeError:
            continue
    st.error("PaddleOCR 초기화 실패: 설치된 버전이 인자들을 지원하지 않습니다.")
    st.stop()


def _prep_im_for_ocr(pil_img: Image.Image, max_side: int = 2000) -> np.ndarray:
    """PIL -> 안전 BGR, 긴 변 max_side로 축소(안정/속도용)"""
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    arr = np.array(pil_img)                 # RGB
    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    h, w = arr.shape[:2]
    m = max(h, w)
    if m > max_side:
        scale = max_side / float(m)
        arr = cv2.resize(arr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
    return np.ascontiguousarray(arr)

def _group_runs(pages):
    """예: [3,4,5, 9,10] -> [(3,5), (9,10)] (연속 구간 묶기)"""
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
def pdf_pages_to_texts(
    pdf_bytes: bytes,
    *,
    dpi: int = 120,
    min_chars_for_pdftext: int = 10,
):
    """
    1) 내장 텍스트 우선
    2) 커버리지에 따라 자동 정책:
       - >=70%: 텍스트만
       - 30~70%: 하이브리드(부족 페이지만 OCR)
       - <30%: 전체 OCR
    return: [(page_no, text), ...], total_pages
    """
    # 1) 내장 텍스트
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        base_pages = [(i+1, (p.extract_text() or "")) for i, p in enumerate(reader.pages)]
    except Exception:
        base_pages = []
    total_pages = len(base_pages)

    # 내장 텍스트 자체가 없으면 → 전체 OCR 시도
    if total_pages == 0:
        try:
            images = convert_from_bytes(pdf_bytes, dpi=dpi)
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
        st.caption("모드: 전체 OCR (내장 텍스트 없음)")
        return out, len(images)

    # 2) 커버리지 계산
    lengths = [len((t or "").strip()) for _, t in base_pages]
    text_pages = sum(1 for L in lengths if L >= min_chars_for_pdftext)
    coverage = text_pages / max(1, total_pages)

    if coverage >= 0.70:
        # ✅ 내장 텍스트만으로 충분
        st.caption(f"모드: 텍스트만 (커버리지 {coverage:.0%})")
        return base_pages, total_pages

    if coverage < 0.30:
        # 🖨 스캔본 판단 → 전체 OCR
        try:
            images = convert_from_bytes(pdf_bytes, dpi=dpi)
        except PDFInfoNotInstalledError:
            st.warning("⚠️ Poppler 미설치: 전체 OCR 불가 → 내장 텍스트만 사용")
            st.caption(f"모드: 텍스트만 (커버리지 {coverage:.0%}, OCR 불가)")
            return base_pages, total_pages
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
        st.caption(f"모드: 전체 OCR (커버리지 {coverage:.0%})")
        return out, len(images)

    # 3) 하이브리드: 부족 페이지만 OCR (연속 구간 묶어서 렌더링 최소화)
    need_pages = [pg for (pg, t) in base_pages if len((t or "").strip()) < min_chars_for_pdftext]
    runs = _group_runs(need_pages)
    page_to_text = {pg: (t or "") for pg, t in base_pages}
    ocr = get_ocr()

    done = 0
    prog = st.progress(0.0, text=f"하이브리드: 부족 페이지만 OCR 중… (총 {len(need_pages)}p, DPI={dpi})")
    for s, e in runs:
        try:
            imgs = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=s, last_page=e)
        except PDFInfoNotInstalledError:
            st.warning("⚠️ Poppler 미설치: OCR 보충 생략 → 내장 텍스트만 사용")
            break
        for idx, pg in enumerate(range(s, e+1)):
            arr = _prep_im_for_ocr(imgs[idx], max_side=2000)
            res = ocr.ocr(arr)
            t2 = "\n".join("".join([w[0] for w in line]) for line in (res[0] or [])) if res else ""
            page_to_text[pg] = t2
            done += 1
            prog.progress(done / max(1, len(need_pages)))
        del imgs
    prog.empty()
    out = [(pg, page_to_text.get(pg, "")) for pg, _ in base_pages]
    st.caption(f"모드: 하이브리드 (커버리지 {coverage:.0%}, OCR {len(need_pages)}p)")
    return out, total_pages


# ===== RAG 유틸 가져오기 =====
try:
    from lib.rag_utils import (
        upsert_doc, doc_exists, _sha1_bytes,
        rag_summarize_section, format_context
    )
except Exception:
    st.error("❌ lib/rag_utils.py 를 찾을 수 없거나 최신 버전이 아닙니다.\n"
             "이전에 제공한 bge-m3 통합판을 저장했는지 확인하세요.")
    st.stop()

# ====== 텍스트/요약 유틸 ======
def extract_pdf_text_if_possible(pdf_file) -> list[tuple[int, str]]:
    """페이지별 내장 텍스트 추출(없으면 빈 문자열). return [(page_no, text), ...]"""
    try:
        reader = PdfReader(pdf_file)
        return [(i+1, (p.extract_text() or "")) for i, p in enumerate(reader.pages)]
    except Exception:
        return []

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

# ===== OCR 보조 유틸(간단 리사이즈) =====
def _prep_im_for_ocr(pil_img: Image.Image, max_side: int = 2000) -> np.ndarray:
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    arr = np.array(pil_img)                         # RGB
    arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)      # BGR
    h, w = arr.shape[:2]
    m = max(h, w)
    if m > max_side:
        scale = max_side / float(m)
        arr = cv2.resize(arr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
    return np.ascontiguousarray(arr)

# ======== PDF → 페이지별 텍스트 (내장 텍스트 우선, OCR은 토글로) ========
@st.cache_data(show_spinner=False)
def pdf_pages_to_texts(
    pdf_bytes: bytes,
    *,
    dpi: int = 120,
    min_chars_for_pdftext: int = 10,
    use_ocr: bool = False,   # 기본 False면 OCR 아예 안 함
):
    """
    1) 내장 텍스트 우선
    2) use_ocr=True일 때만 부족한 페이지만 이미지 렌더링 + OCR
    return: [(page_no, text), ...], total_pages
    """
    # 1) 내장 텍스트
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        base_pages = [(i+1, (p.extract_text() or "")) for i, p in enumerate(reader.pages)]
    except Exception:
        base_pages = []
    total_pages = len(base_pages)

    # 내장 텍스트가 전혀 없을 때
    if total_pages == 0:
        if not use_ocr:
            return [], 0
        # 전체 OCR
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
            del img; gc.collect()
        prog.empty()
        return out, len(images)

    # 내장 텍스트가 "있을" 때
    if not use_ocr:
        # ✅ OCR 끔: 내장 텍스트만 사용 → 가장 빠름
        return base_pages, total_pages

    # OCR 켬: "짧은" 페이지만 보충
    out, prog = [], st.progress(0.0, text=f"부족 페이지만 OCR 보충 중… (DPI={dpi})")
    ocr = get_ocr()
    for i, (pg, t) in enumerate(base_pages, start=1):
        s = (t or "").strip()
        if len(s) >= min_chars_for_pdftext:
            out.append((pg, t))
        else:
            try:
                kw = {"dpi": dpi, "first_page": pg, "last_page": pg}
                if POPPLER_PATH: kw["poppler_path"] = POPPLER_PATH
                img = convert_from_bytes(pdf_bytes, **kw)[0]
                arr = _prep_im_for_ocr(img, max_side=2000)
                res = ocr.ocr(arr)
                t2 = "\n".join("".join([w[0] for w in line]) for line in (res[0] or [])) if res else ""
            except PDFInfoNotInstalledError:
                st.warning("⚠️ Poppler 미설치: 해당 페이지 OCR 건너뜀")
                t2 = t or ""
            out.append((pg, t2))
            del img; gc.collect()
        prog.progress(i/total_pages)
    prog.empty()
    return out, total_pages

# ====== UI 상태 ======
if "file_key" not in st.session_state:
    st.session_state.file_key = "uploader_1"

st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
if st.button("🔄 전체 새로고침", key="refresh_all"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state.file_key = "uploader_" + str(np.random.randint(100000))
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

st.title("🐾 딸깍공 · PDF 요약 (RAG + 선택 구간)")

uploaded = st.file_uploader("PDF 파일 업로드", type=["pdf"], key=st.session_state.file_key)
if not uploaded:
    st.info("PDF를 업로드하면 **페이지별 텍스트 확보** → (필요시) **벡터DB 인덱싱** → 원하는 **페이지 범위만 RAG 요약**합니다.")
    st.stop()

pdf_bytes = uploaded.read()


# ====== 페이지 텍스트 확보(내장 텍스트 우선, 필요시만 OCR) ======
with st.spinner("PDF 페이지 텍스트 확보 중…"):
    pages_text, total_pages = pdf_pages_to_texts(
        pdf_bytes,
        dpi=120,                  # 렌더링 부담↓
        min_chars_for_pdftext=10  # OCR 트리거 최소화
    )

if total_pages == 0:
    st.error("PDF에서 페이지를 찾지 못했습니다.")
    st.stop()

# ====== 인덱싱 (이미 있으면 스킵) ======
from lib.rag_utils import upsert_doc  # 재확인
doc_id_guess = _sha1_bytes(pdf_bytes)
if doc_exists(doc_id_guess):
    added, doc_id = 0, doc_id_guess
    st.info(f"✅ 이미 인덱싱됨: doc_id={doc_id} (업서트 생략)")
else:
    with st.spinner("벡터DB 인덱싱 중… (재인덱싱 방지)"):
        added, doc_id = upsert_doc(
            pages_text,
            source_name=uploaded.name,
            file_bytes=pdf_bytes,    # 같은 파일이면 같은 doc_id
            chunk_size=800, overlap=200,
            force=False
        )

st.success(f"📦 인덱싱 상태 — 페이지 {total_pages} / 신규 청크 {added}개 (doc_id: {doc_id})")
st.session_state.current_doc_id = doc_id
st.session_state.total_pages = total_pages

# ====== 선택 구간 요약 UI ======
st.subheader("📌 요약 구간 선택")
page_s, page_e = st.slider("페이지 범위", 1, total_pages, (1, min(5, total_pages)))
query = st.text_input("요약 주제/질문(선택, 공백이면 '핵심 요약')", value="핵심 요약")

colA, colB = st.columns([1,1])
with colA:
    if st.button("📝 선택 구간만 RAG 요약", use_container_width=True):
        with st.spinner("선택 구간 컨텍스트 검색 및 요약 중…"):
            out = rag_summarize_section(
                client=client,
                model=MODEL_SUMMARY,
                doc_id=doc_id,
                query=query or "핵심 요약",
                page_range=(page_s, page_e),
                max_chars_context=9000,
                top_k=16
            )
        st.markdown("### ✅ 요약 결과 (선택 구간)")
        st.write(out["summary"])
        with st.expander("🔎 근거 컨텍스트 보기"):
            st.code(format_context(out["evidence"]))

with colB:
    if st.button("📄 전체 문서 일반 요약", use_container_width=True):
        all_text = "\n\n".join([t for _, t in pages_text])
        res = summarize_content(all_text)
        st.markdown("### 🧾 전체 요약 (일반)")
        st.write(res)

    if st.button("🧠 전체 문서 RAG 요약(근거)", use_container_width=True):
        with st.spinner("전체 문서 컨텍스트 검색(RAG) 및 요약 중…"):
            out = rag_summarize_section(
                client=client,
                model=MODEL_SUMMARY,
                doc_id=doc_id,
                query=(query or "전체 핵심 요약"),
                page_range=(1, total_pages),
                max_chars_context=9000,
                top_k=16
            )
        st.markdown("### ✅ 전체 문서 RAG 요약 (근거 포함)")
        st.write(out["summary"])
        with st.expander("🔎 근거 컨텍스트 보기"):
            st.code(format_context(out["evidence"]))
