# -*- coding: utf-8 -*-
import streamlit as st
from lib.settings import get_openai_client
from lib.rag_utils import retrieve_snippets_for_doc, cap_by_chars, format_context

def target_lines_for_length(n_chars: int) -> int:
    if n_chars < 1500: return 4
    if n_chars < 5000: return 6
    if n_chars < 12000: return 8
    if n_chars < 25000: return 10
    if n_chars < 50000: return 13
    return 16

def summarize_doc_with_rag(doc_id: str, *, target_lines: int, max_chars: int = 12000, top_k: int = 18, model="gpt-4o-mini"):
    query = f"이 문서의 핵심을 {max(2, target_lines-1)}~{target_lines+1}줄로, 숫자/고유명사 보존하며 정리"
    snips = retrieve_snippets_for_doc(doc_id, query=query, n_initial=40, top_k=top_k)
    snips = cap_by_chars(snips, max_chars=max_chars)
    context = format_context(snips)

    sys = ("주어진 CONTEXT 안의 정보만 사용해 한국어로 요약해라. "
           "모르면 모른다고 답해라. 마지막 줄에 참조 번호를 [1][3] 형식으로 붙여라.")
    user = f"CONTEXT:\n{context}\n\n요청:\n{query}"

    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":sys},{"role":"user","content":user}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip(), snips
