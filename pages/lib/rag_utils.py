# lib/rag_utils.py
# -*- coding: utf-8 -*-
"""
bge-m3 최적화 RAG 유틸 (Streamlit 친화):
- 임베더 로드/캐시(get_embedder): GPU면 FP16/TF32
- 임베딩(embed_texts): bge-m3 권장 prefix 자동 적용 (query:/passage:)
- 영구 벡터 스토어(get_store): CHROMA_DB_PATH 또는 ./vectorstore
- 재인덱싱 방지(upsert_doc): 이미 있으면 스킵(force=True로 강제 갱신)
- 검색(retrieve_snippets_for_doc): 페이지 범위 where 필터 + query_embeddings 직접 주입
- MMR 재순위(_mmr): 같은 임베더로 문서 임베딩 후 다양성/관련성 균형
- 요약(rag_summarize_section): 컨텍스트 밖 지식 금지 + [#] 인용
"""
import os
import hashlib, uuid, math
import numpy as np
import streamlit as st
from typing import List, Tuple, Dict, Optional, Any
import torch
from functools import lru_cache

# ====== Chroma Persistent Store ======
import chromadb

# =========================
# bge-m3 세팅
# =========================
BGE_MODEL_NAME = "BAAI/bge-m3"
BGE_QUERY_PREFIX = "query: "
BGE_DOC_PREFIX   = "passage: "

try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass

@lru_cache(maxsize=1)
def get_embedder():
    """SentenceTransformer 임베더 1회 로드 + GPU FP16/TF32 최적화"""
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(BGE_MODEL_NAME, device=device)
    if device == "cuda":
        try:
            model = model.half()
            torch.backends.cuda.matmul.allow_tf32 = True
        except Exception:
            pass
    return model

def embed_texts(
    texts: List[str],
    *,
    task: str = "doc",               # "doc" | "query"
    batch_size: Optional[int] = None,
    normalize: bool = True,
    add_instruction: bool = True,
) -> np.ndarray:
    """texts(list[str]) -> np.ndarray [N, D]  (bge 권장 prefix 자동 적용)"""
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    if add_instruction:
        if task == "query":
            texts = [BGE_QUERY_PREFIX + (t or "") for t in texts]
        else:
            texts = [BGE_DOC_PREFIX + (t or "") for t in texts]

    emb = get_embedder()
    if batch_size is None:
        batch_size = 128 if torch.cuda.is_available() else 32

    with torch.inference_mode():
        vecs = emb.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
    return vecs

# =========================
# Chroma Store
# =========================
def _db_path() -> str:
    return os.getenv("CHROMA_DB_PATH", os.path.abspath("vectorstore"))

@st.cache_resource(show_spinner=False)
def get_store():
    """
    Persistent Chroma + collection (쿼리 임베딩은 우리가 직접 넣을 것이므로
    embedding_function 미설정; 문서 업서트 시에도 precomputed embeddings 사용)
    """
    client = chromadb.PersistentClient(path=_db_path())
    coll = client.get_or_create_collection(
        name="docs",
        metadata={"hnsw:space": "cosine"},
    )

    # 외부 호환을 위해 ef 래퍼를 제공(내부적으로 우리 embed_texts 사용)
    def ef(texts: List[str], *, task: str = "doc") -> np.ndarray:
        return embed_texts(texts, task=task, normalize=True, add_instruction=True)

    return client, coll, ef

# =========================
# 청크
# =========================
def _chunk_page_text(pages: List[Tuple[int, str]], chunk_size=800, overlap=200, doc_id="doc"):
    chunks, metas = [], []
    for pg, txt in (pages or []):
        s = (txt or "").strip()
        if not s:
            continue
        i, cidx, L = 0, 0, len(s)
        while i < L:
            j = min(L, i + chunk_size)
            ch = s[i:j]
            chunks.append(ch)
            metas.append({"doc_id": doc_id, "page": pg, "chunk": f"p{pg}_c{cidx}"})
            cidx += 1
            if j == L:
                break
            i = max(0, j - overlap)
    return chunks, metas

def _sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]

# =========================
# 존재 여부
# =========================
def doc_exists(doc_id: str) -> bool:
    _, coll, _ = get_store()
    try:
        res = coll.get(where={"doc_id": doc_id}, limit=1)
    except TypeError:
        res = coll.get(where={"doc_id": doc_id})
    return bool(res.get("ids"))

# =========================
# 업서트 (재인덱싱 방지)
# =========================
def upsert_doc(
    pages_text: List[Tuple[int, str]],
    source_name: str,
    *,
    chunk_size=800,
    overlap=200,
    file_bytes: Optional[bytes] = None,
    force: bool = False,     # ✅ 이미 있으면 스킵. 강제 갱신 시 True
):
    client, coll, _ = get_store()

    # 문서 UID: 파일바이트 우선, 없으면 텍스트 기반
    doc_uid_bytes = file_bytes or "\n".join((t or "") for _, t in pages_text).encode("utf-8")
    doc_id = _sha1_bytes(doc_uid_bytes)

    # 이미 인덱싱되어 있으면 스킵
    if (not force) and doc_exists(doc_id):
        return 0, doc_id

    # force=True면 기존 문서 제거 후 새로 업서트
    if force:
        try:
            coll.delete(where={"doc_id": doc_id})
        except Exception:
            pass

    # 청크 생성
    chunks, metas = _chunk_page_text(
        pages_text, chunk_size=chunk_size, overlap=overlap, doc_id=doc_id
    )
    if not chunks:
        return 0, doc_id

    ids = [f"{doc_id}_{i+1}" for i in range(len(chunks))]
    metas = [{**m, "source": source_name} for m in metas]

    # 임베딩 (진행률 표시)
    B = 128 if torch.cuda.is_available() else 64
    vecs = []
    prog = st.progress(0.0, text=f"임베딩 계산 중… (배치 {B})")
    total_batches = (len(chunks) + B - 1) // B
    for bi in range(0, len(chunks), B):
        batch = chunks[bi:bi+B]
        v = embed_texts(batch, task="doc", add_instruction=True)
        vecs.append(v)
        done = (bi // B) + 1
        prog.progress(done / total_batches)
    prog.empty()
    embs = np.vstack(vecs).tolist()

    # 벡터DB 저장 (진행률 표시)
    B2 = 256
    prog2 = st.progress(0.0, text="벡터DB에 저장 중…")
    total_batches2 = (len(chunks) + B2 - 1) // B2
    for bi in range(0, len(chunks), B2):
        coll.add(
            ids=ids[bi:bi+B2],
            documents=chunks[bi:bi+B2],
            metadatas=metas[bi:bi+B2],
            embeddings=embs[bi:bi+B2],
        )
        done2 = (bi // B2) + 1
        prog2.progress(done2 / total_batches2)
    prog2.empty()

    return len(chunks), doc_id

# =========================
# 검색 + MMR
# =========================
def _build_where(doc_id: str, page_range: Optional[Tuple[int, int]]):
    # Chroma 최신 필터: 루트에 하나의 연산자만 허용
    if page_range and len(page_range) == 2:
        s, e = int(page_range[0]), int(page_range[1])
        return {
            "$and": [
                {"doc_id": doc_id},         # 동등 비교는 이렇게 써도 됨
                {"page": {"$gte": s}},      # 범위 조건을 개별 항목으로 분리
                {"page": {"$lte": e}},
            ]
        }
    # 단일 조건이라도 일관성 위해 $and로 감싸도 무방
    return {"$and": [{"doc_id": doc_id}]}


def _l2n(x: np.ndarray):
    n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-9
    return x / n

def _mmr(docs: List[Tuple[str, Dict]], query: str, top_k=8, lambda_mult=0.6):
    """
    docs: [(text, meta), ...]
    같은 임베더로 문서/질의 임베딩 → 관련성/다양성 균형
    """
    texts = [d[0] for d in docs]
    if not texts:
        return []
    E = _l2n(embed_texts(texts, task="doc", add_instruction=True))
    q = _l2n(embed_texts([query], task="query", add_instruction=True))[0]
    rel = E @ q
    selected = [int(np.argmax(rel))]
    cand = set(range(len(texts))) - set(selected)

    while len(selected) < min(top_k, len(texts)) and cand:
        best, best_score = None, -1e9
        for i in list(cand):
            div = float(np.max(E[i] @ E[selected].T))
            score = lambda_mult * float(rel[i]) - (1 - lambda_mult) * div
            if score > best_score:
                best, best_score = i, score
        selected.append(best)
        cand.remove(best)

    return [docs[i] for i in selected]

def retrieve_snippets_for_doc(
    doc_id: str,
    query: str,
    *,
    n_initial=40,
    top_k=18,
    page_range: Optional[Tuple[int, int]] = None,
    soft_expand: bool = True,
) -> List[Tuple[str, Dict]]:
    """
    페이지 범위(where) 우선 검색 → (부족 시) 문서 전체로 보충 → MMR 재순위
    return: [(text, metadata), ...]
    """
    _, coll, _ = get_store()

    # 질의 임베딩을 우리가 직접 넣음(일관 파이프라인)
    qvec = embed_texts([query], task="query", add_instruction=True)[0]

    # 1) 선택 구간만 검색
    where = _build_where(doc_id, page_range)
    res = coll.query(
        query_embeddings=[qvec],
        n_results=min(n_initial, 100),
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    docs = list(zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]))

    # 2) 범위가 빈약하면 문서 전체로 보충(중복 제거)
    if soft_expand and len(docs) < max(6, top_k // 2):
        res_all = coll.query(
            query_embeddings=[qvec],
            n_results=min(n_initial, 100),
            where={"doc_id": doc_id},
            include=["documents", "metadatas", "distances"],
        )
        docs_all = list(zip(res_all.get("documents", [[]])[0], res_all.get("metadatas", [[]])[0]))
        seen, merged = set(), []
        for pair in docs + docs_all:
            key = (pair[0], tuple(sorted(pair[1].items())))
            if key not in seen:
                seen.add(key)
                merged.append(pair)
        docs = merged

    if not docs:
        return []

    # 3) MMR 재순위
    return _mmr(docs, query, top_k=top_k, lambda_mult=0.6)

# =========================
# 컨텍스트 유틸
# =========================
def cap_by_chars(snips: List[Tuple[str, Dict]], max_chars=12000):
    out, used = [], 0
    for t, m in snips:
        L = len(t or "")
        if used + L <= max_chars:
            out.append((t, m))
            used += L
        else:
            r = max_chars - used
            if r > 400:
                out.append(((t or "")[:r], m))
            break
    return out

def format_context(snips: List[Tuple[str, Dict]]):
    blocks = []
    for i, (t, m) in enumerate(snips, start=1):
        tag = f"[{i}] ({m.get('source','?')} p.{m.get('page','?')} {m.get('chunk','?')})"
        blocks.append(f"{tag}\n{t}")
    return "\n\n---\n\n".join(blocks)

# =========================
# RAG 요약
# =========================
def rag_summarize_section(
    client: Any,
    model: str,
    doc_id: str,
    query: str,
    page_range: Tuple[int, int],
    *,
    max_chars_context: int = 9000,
    top_k: int = 16,
) -> Dict[str, Any]:
    """
    선택 구간만 요약 (부족 시 soft expand 보조)
    returns: {"summary": str, "evidence": List[(text, meta)]}
    """
    snips = retrieve_snippets_for_doc(
        doc_id, query, n_initial=40, top_k=top_k, page_range=page_range, soft_expand=True
    )
    if not snips:
        return {
            "summary": f"선택한 구간(p.{page_range[0]}–{page_range[1]})에서 요약할 텍스트를 찾지 못했습니다.",
            "evidence": [],
        }

    snips = cap_by_chars(snips, max_chars=max_chars_context)
    ctx = format_context(snips)

    system = (
        "You are a focused summarizer for a study app.\n"
        "Use ONLY the provided context. Do NOT add external knowledge.\n"
        "Cite evidence using [#] indices that match the context blocks."
    )
    user = f"""
[Task]
Summarize ONLY the selected page range p.{page_range[0]}–{page_range[1]} for the query:
{query}

[Style]
- Bullet points (3–7 bullets)
- Be concise and faithful to the context
- Each important claim ends with a citation like [3] or [1][4]
- If the answer isn't in the context, say so.

[Context]
{ctx}
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system", "content": system},
            {"role":"user",   "content": user},
        ],
        temperature=0.2,
    )
    summary = resp.choices[0].message.content.strip()
    return {"summary": summary, "evidence": snips}
