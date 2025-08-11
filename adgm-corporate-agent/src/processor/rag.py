# src/processor/rag.py
# RAG module (index building + retrieval) using OpenAI embeddings and FAISS.
# IMPORTANT: set OPENAI_API_KEY in environment before running the build script.

import os
import json
import faiss
import numpy as np
from typing import List, Dict, Tuple
import logging
import pdfplumber
import re
import openai

EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _read_pdf_text(path: str) -> List[Tuple[int, str]]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append((i, text))
    return pages

def _clean_text(s: str) -> str:
    s = re.sub(r"\\n\\s*\\n+", "\\n\\n", s)
    return s.strip()

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    text = _clean_text(text)
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = max(start + chunk_size - overlap, start + 1)
    return chunks

def _ensure_openai_key():
    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError("OPENAI_API_KEY env var not set. Please set it to use embeddings.")

def _embed_texts(texts: List[str]) -> List[List[float]]:
    _ensure_openai_key()
    openai.api_key = os.environ["OPENAI_API_KEY"]
    embeddings = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = openai.Embeddings.create(model=EMBED_MODEL, input=batch)
        for d in resp["data"]:
            embeddings.append(d["embedding"])
    return embeddings

def build_index_from_corpus(corpus_dir: str, index_path: str, meta_path: str,
                            chunk_size: int = 800, overlap: int = 100):
    logger.info("Building index from corpus: %s", corpus_dir)
    docs = []
    for root, _, files in os.walk(corpus_dir):
        for fname in files:
            if fname.lower().endswith(".pdf") or fname.lower().endswith(".txt"):
                full = os.path.join(root, fname)
                if fname.lower().endswith(".pdf"):
                    pages = _read_pdf_text(full)
                    for (page_no, page_text) in pages:
                        if page_text and page_text.strip():
                            chunks = _chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)
                            for ci, ch in enumerate(chunks):
                                docs.append({
                                    "source": full,
                                    "page": page_no,
                                    "chunk_index": ci,
                                    "text": ch
                                })
                else:
                    with open(full, "r", encoding="utf-8") as f:
                        txt = f.read()
                        chunks = _chunk_text(txt, chunk_size=chunk_size, overlap=overlap)
                        for ci, ch in enumerate(chunks):
                            docs.append({
                                "source": full,
                                "page": None,
                                "chunk_index": ci,
                                "text": ch
                            })

    if not docs:
        raise ValueError("No documents found in corpus_dir: " + corpus_dir)

    texts = [d["text"] for d in docs]
    embeddings = _embed_texts(texts)

    xb = np.array(embeddings).astype("float32")
    d = xb.shape[1]
    logger.info("Embedding dimension: %s; nb vectors: %s", d, xb.shape[0])

    index = faiss.IndexFlatL2(d)
    index.add(xb)
    faiss.write_index(index, index_path)
    for i, dmeta in enumerate(docs):
        dmeta["_id"] = i
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    logger.info("Index built and saved to %s (meta: %s)", index_path, meta_path)

def _load_index_and_meta(index_path: str, meta_path: str):
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta

def get_citation_for_issue(query: str, index_path: str, meta_path: str, top_k: int = 3) -> Dict:
    _ensure_openai_key()
    openai.api_key = os.environ["OPENAI_API_KEY"]
    index, meta = _load_index_and_meta(index_path, meta_path)
    q_emb = _embed_texts([query])[0]
    qx = np.array([q_emb]).astype("float32")
    D, I = index.search(qx, top_k)
    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0 or idx >= len(meta):
            continue
        m = meta[idx]
        results.append({
            "score": float(score),
            "source": m["source"],
            "page": m.get("page"),
            "chunk_index": m.get("chunk_index"),
            "text": m.get("text")
        })
    passages = "\\n\\n---\\n\\n".join([r["text"] for r in results])
    prompt = (
        "You are a legal assistant. Given this query and the retrieved passages from ADGM documents, "
        "produce a one-sentence citation (with which document/file and page) that supports or explains the query, "
        "and extract a short quoted passage (<= 120 words) that is most relevant. "
        "If nothing relevant is found, say 'no relevant passage found'.\\n\\n"
        f"QUERY: {query}\\n\\nRETRIEVED_PASSAGES:\\n{passages}\\n\\n"
        "Output JSON with keys: citation (string), excerpt (string)."
    )
    resp = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.0
    )
    llm_text = resp["choices"][0]["message"]["content"].strip()
    try:
        import json as _json
        llm_json = _json.loads(llm_text)
    except Exception:
        llm_json = {"citation": llm_text, "excerpt": ""}
    return {
        "query": query,
        "results": results,
        "llm_summary": llm_json
    }