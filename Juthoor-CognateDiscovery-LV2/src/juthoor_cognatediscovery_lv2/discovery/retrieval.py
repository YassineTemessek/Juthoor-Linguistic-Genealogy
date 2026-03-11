"""
Retrieval orchestration for LV2.
Handles embedding, indexing, and searching.
"""
from __future__ import annotations

import hashlib
import numpy as np
from pathlib import Path
from typing import Any

from juthoor_cognatediscovery_lv2.lv3.discovery.embeddings import (
    BgeM3Config, BgeM3Embedder, ByT5Config, ByT5Embedder, GeminiConfig, GeminiEmbedder
)
from juthoor_cognatediscovery_lv2.lv3.discovery.index import FaissIndex, build_flat_ip
from juthoor_cognatediscovery_lv2.lv3.discovery.jsonl import LexemeRow, read_jsonl_rows, write_jsonl
from .corpora import CorpusSpec


def resolve_corpus_path(spec: CorpusSpec, repo_root: Path) -> Path:
    path = spec.path
    if path.is_absolute():
        return path.resolve()
    if path.exists():
        return path.resolve()
    cwd_candidate = (Path.cwd() / path)
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    return (repo_root / path).resolve()


def _rows_signature(rows: list[LexemeRow]) -> str:
    joined = "|".join(row.lexeme_id for row in rows)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


def _corpus_cache_key(spec: CorpusSpec, repo_root: Path, rows: list[LexemeRow] | None = None) -> str:
    resolved = resolve_corpus_path(spec, repo_root)
    stem = resolved.stem or "corpus"
    safe_stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem)
    digest_source = str(resolved)
    if rows is not None:
        digest_source = f"{digest_source}|n={len(rows)}|sig={_rows_signature(rows)}"
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
    return f"{safe_stem}_{digest}"


def load_lexemes(spec: CorpusSpec, repo_root: Path, limit: int = 0) -> list[LexemeRow]:
    path = resolve_corpus_path(spec, repo_root)
    return read_jsonl_rows(path, limit=limit)

def get_cache_paths(
    repo_root: Path,
    model: str,
    spec: CorpusSpec,
    rows: list[LexemeRow] | None = None,
) -> tuple[Path, Path, Path, Path]:
    base = repo_root / "outputs"
    corpus_key = _corpus_cache_key(spec, repo_root, rows)
    embeddings_dir = base / "embeddings" / model / spec.lang / (spec.stage or "unknown") / corpus_key
    vectors_path = embeddings_dir / "vectors.npy"
    rows_path = embeddings_dir / "rows.jsonl"

    indexes_dir = base / "indexes" / model / spec.lang / (spec.stage or "unknown") / corpus_key
    index_path = indexes_dir / "index.faiss"
    meta_path = indexes_dir / "meta.json"
    return vectors_path, rows_path, index_path, meta_path

def embed_corpus(
    *,
    repo_root: Path,
    model: str,
    spec: CorpusSpec,
    rows: list[LexemeRow],
    device: str = "cpu",
    semantic_cfg: BgeM3Config | None = None,
    form_cfg: ByT5Config | None = None,
    rebuild_cache: bool = False,
    backend: str = "local",
):
    cache_model = f"api_{model}" if backend == "api" else model
    v_path, r_path, _, _ = get_cache_paths(repo_root, cache_model, spec, rows)

    if not rebuild_cache and v_path.exists() and r_path.exists():
        vecs = np.load(v_path)
        cached_rows = read_jsonl_rows(r_path, limit=0)
        return vecs, cached_rows

    # Field-aware text selection
    texts: list[str] = []
    for r in rows:
        if model == "semantic":
            # Priority: meaning_text -> gloss_plain -> lemma
            t = r.data.get("meaning_text") or r.data.get("gloss_plain") or r.lemma
        else:
            # Priority: form_text -> ipa -> translit -> lemma
            t = r.data.get("form_text") or r.data.get("ipa") or r.data.get("translit") or r.lemma
        
        t = " ".join(str(t or "").split()).strip()
        texts.append(t if t else r.lexeme_id)

    if backend == "api":
        task = "SEMANTIC_SIMILARITY" if model == "semantic" else "RETRIEVAL_DOCUMENT"
        embedder = GeminiEmbedder(config=GeminiConfig(task_type=task, dimensions=1024))
        vecs = embedder.embed(texts)
    elif model == "semantic":
        embedder = BgeM3Embedder(config=semantic_cfg or BgeM3Config())
        vecs = embedder.embed(texts)
    elif model == "form":
        embedder = ByT5Embedder(config=form_cfg or ByT5Config(), device=device)
        vecs = embedder.embed(texts)
    else:
        raise ValueError(f"Unknown model {model!r}.")

    v_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(v_path, vecs)
    write_jsonl(r_path, (r.data | {"_row_idx": r.row_idx} for r in rows))
    return vecs, rows

def build_or_load_index(
    *,
    repo_root: Path,
    model: str,
    spec: CorpusSpec,
    vectors: np.ndarray,
    rows: list[LexemeRow],
    rebuild_index: bool,
):
    cache_model = model # already prefixed if api
    _, _, index_path, meta_path = get_cache_paths(repo_root, cache_model, spec, rows)
    
    idx_meta = FaissIndex(index_path=index_path, meta_path=meta_path, dim=int(vectors.shape[1]))
    if not rebuild_index and index_path.exists():
        return idx_meta.load()

    index, dim = build_flat_ip(vectors)
    idx_meta = FaissIndex(index_path=index_path, meta_path=meta_path, dim=dim)
    idx_meta.save(index)
    return index

def search_index(index, query_vectors: np.ndarray, topk: int):
    topk = int(topk)
    if topk <= 0:
        raise ValueError("topk must be > 0")
    scores, idxs = index.search(np.asarray(query_vectors, dtype="float32"), topk)
    return scores, idxs
