# -*- coding: utf-8 -*-
import time
import numpy as np
import streamlit as st
from io import BytesIO
from typing import List, Tuple
from PIL import Image
from paddleocr import PaddleOCR

# 선택 라이브러리
try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except Exception:
    PYMUPDF_OK = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_OK = True
except Exception:
    PYPDF2_OK = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_OK = True
except Exception:
    PDF2IMAGE_OK = False

@st.cache_resource(show_spinner=False)
def get_ocr():
    # 안정 파라미터만 사용 (show_log 같은 미지원 인자 금지)
    return PaddleOCR(lang="korean", use_angle_cls=True)

def _np_rgb(pil: Image.Image):
    return np.array(pil.convert("RGB"))

def ocr_image_pil(pil: Image.Image) -> str:
    """단일 이미지 OCR → 텍스트 라인 합치기"""
    try:
        res = get_ocr().ocr(_np_rgb(pil)) or []
        lines = []
        for page in res:
            for item in page:
                # item: [bbox, (text, score)]
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    t = item[1][0]
                    lines.append(str(t))
        return "\n".join(lines).strip()
    except Exception as e:
        st.warning(f"OCR 실패: {e}")
        return ""

def extract_pdf_text_pymupdf(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """PyMuPDF로 텍스트 레이어 추출"""
    pages = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in range(doc.page_count):
        t = (doc.load_page(i).get_text("text") or "").strip()
        pages.append((i + 1, t))
    doc.close()
    return pages

def extract_pdf_text_pypdf2(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """PyPDF2로 텍스트 레이어 추출"""
    pages = []
    r = PdfReader(BytesIO(pdf_bytes))
    for i, p in enumerate(r.pages, start=1):
        t = (p.extract_text() or "").strip()
        pages.append((i, t))
    return pages

def extract_pdf_text_hybrid(pdf_bytes: bytes, min_text_len=50, dpi=180):
    """
    1) 텍스트 레이어 우선(PyMuPDF → PyPDF2)
    2) 빈약한 페이지만 pdf2image로 변환 후 OCR
    return: (pages_text, used_ocr_pages)
      - pages_text: [(page, text), ...] (전체 페이지)
      - used_ocr_pages: OCR가 적용된 페이지 번호 set
    """
    # 1) 텍스트 레이어
    pages = []
    if PYMUPDF_OK:
        try:
            pages = extract_pdf_text_pymupdf(pdf_bytes)
        except Exception:
            pages = []
    if not pages and PYPDF2_OK:
        try:
            pages = extract_pdf_text_pypdf2(pdf_bytes)
        except Exception:
            pages = []

    if not pages:
        # 텍스트 레이어 추출 실패 → 전 페이지 OCR
        used = set()
        if not PDF2IMAGE_OK:
            st.error("pdf2image/Poppler 미설치: 텍스트 레이어도 없어서 OCR이 불가합니다.")
            return [], used
        pil_pages = convert_from_bytes(pdf_bytes, dpi=dpi)
        texts, prog = [], st.progress(0.0, text="PDF OCR 중…")
        for i, pil in enumerate(pil_pages, start=1):
            texts.append((i, ocr_image_pil(pil)))
            used.add(i)
            prog.progress(i / len(pil_pages))
        prog.empty()
        return texts, used

    # 2) 빈약한 페이지만 OCR
    need_ocr = [pg for (pg, t) in pages if len((t or "").strip()) < min_text_len]
    used = set()
    if need_ocr and PDF2IMAGE_OK:
        prog = st.progress(0.0, text="빈약 페이지 OCR 보강 중…")
        for k, pg in enumerate(need_ocr, start=1):
            try:
                pil = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=pg, last_page=pg)[0]
                t = ocr_image_pil(pil)
                pages[pg - 1] = (pg, (t or ""))
                used.add(pg)
            except Exception:
                pass
            prog.progress(k / len(need_ocr))
        prog.empty()
    elif need_ocr and not PDF2IMAGE_OK:
        st.info("pdf2image/Poppler 미설치로 빈약 페이지 OCR 보강은 생략되었습니다.")

    pages.sort(key=lambda x: x[0])
    return pages, used
