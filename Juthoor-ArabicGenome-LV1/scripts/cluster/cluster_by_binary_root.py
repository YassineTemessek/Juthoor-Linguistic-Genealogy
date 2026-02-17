"""
Discovery clustering for Arabic based on LV0-provided `binary_root`.

Purpose (LV2 discovery):
  - Group words by `binary_root`
  - Within each group, produce coarse subclusters using lightweight similarities
    (no heavy model downloads required).

Inputs (default):
  - data/processed/arabic/classical/lexemes.jsonl

Outputs (default):
  - outputs/clusters/binary_root_lemma_clusters.jsonl
  - outputs/clusters/binary_root_similarity_edges.csv
  - outputs/qa/binary_root_coherence.json

Notes:
  - This is discovery-first and intentionally simple. Later we can replace
    similarity functions with embedding-based ones (SONAR/CANINE) while keeping
    the same output contracts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
WS_RE = re.compile(r"\s+")


def strip_arabic_diacritics(text: str) -> str:
    return AR_DIACRITICS_RE.sub("", text or "")


def norm_text(text: str) -> str:
    text = (text or "").strip()
    text = WS_RE.sub(" ", text)
    return text


def char_ngrams(text: str, *, n: int = 2) -> set[str]:
    text = strip_arabic_diacritics(norm_text(text))
    text = text.replace(" ", "")
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(0, len(text) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union) if union else 0.0


def token_set(text: str) -> set[str]:
    text = norm_text(text).lower()
    if not text:
        return set()
    return {t for t in re.split(r"[^0-9a-zA-Z\u0600-\u06FF]+", text) if t}


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


@dataclass(frozen=True)
class LemmaRow:
    lemma: str
    language: str
    script: str
    stage: str
    source: str
    root_norm: str
    binary_root: str
    translit: str
    ipa: str
    gloss: str


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def cluster_indices(sim_matrix: list[list[float]], *, threshold: float) -> list[int]:
    n = len(sim_matrix)
    dsu = DSU(n)
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i][j] >= threshold:
                dsu.union(i, j)
    roots = [dsu.find(i) for i in range(n)]
    # map root -> compact cluster id
    root_to_cluster: dict[int, int] = {}
    next_id = 0
    out: list[int] = []
    for r in roots:
        cid = root_to_cluster.get(r)
        if cid is None:
            cid = next_id
            root_to_cluster[r] = cid
            next_id += 1
        out.append(cid)
    return out


def build_similarity(rows: list[LemmaRow]) -> tuple[list[list[float]], list[list[float]]]:
    # form: char bigram jaccard on lemma (Arabic script)
    # meaning: token jaccard on gloss (or empty)
    form_feats = [char_ngrams(r.lemma, n=2) for r in rows]
    meaning_feats = [token_set(r.gloss) for r in rows]

    n = len(rows)
    form_sim = [[0.0] * n for _ in range(n)]
    meaning_sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        form_sim[i][i] = 1.0
        meaning_sim[i][i] = 1.0
        for j in range(i + 1, n):
            fs = jaccard(form_feats[i], form_feats[j])
            ms = jaccard(meaning_feats[i], meaning_feats[j])
            form_sim[i][j] = form_sim[j][i] = fs
            meaning_sim[i][j] = meaning_sim[j][i] = ms
    return form_sim, meaning_sim


def sample_pairs(indices: Sequence[int], *, max_pairs: int, rng) -> list[tuple[int, int]]:
    if len(indices) < 2:
        return []
    pairs: list[tuple[int, int]] = []
    n = len(indices)
    max_pairs = max(1, int(max_pairs))
    for _ in range(max_pairs):
        i = rng.randrange(n)
        j = rng.randrange(n - 1)
        if j >= i:
            j += 1
        pairs.append((indices[i], indices[j]))
    return pairs


def avg_sim_for_groups(
    *,
    groups: dict[str, list[int]],
    form_feats: list[set[str]],
    meaning_feats: list[set[str]],
    max_pairs: int,
    rng,
) -> dict[str, float]:
    total_form = 0.0
    total_meaning = 0.0
    total_pairs = 0
    for idxs in groups.values():
        pairs = sample_pairs(idxs, max_pairs=max_pairs, rng=rng)
        for i, j in pairs:
            total_form += jaccard(form_feats[i], form_feats[j])
            total_meaning += jaccard(meaning_feats[i], meaning_feats[j])
        total_pairs += len(pairs)
    if total_pairs == 0:
        return {"form_avg": 0.0, "meaning_avg": 0.0, "pairs": 0}
    return {
        "form_avg": total_form / total_pairs,
        "meaning_avg": total_meaning / total_pairs,
        "pairs": total_pairs,
    }


def shuffled_groups(groups: dict[str, list[int]], *, rng) -> dict[str, list[int]]:
    all_indices: list[int] = []
    sizes: list[int] = []
    for idxs in groups.values():
        sizes.append(len(idxs))
        all_indices.extend(idxs)
    rng.shuffle(all_indices)
    out: dict[str, list[int]] = {}
    pos = 0
    for gi, size in enumerate(sizes, start=1):
        out[f"shuf_{gi}"] = all_indices[pos : pos + size]
        pos += size
    return out


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("data/processed/arabic/classical/lexemes.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/clusters"))
    ap.add_argument("--form-threshold", type=float, default=0.55, help="Within-binary_root threshold for form subclusters.")
    ap.add_argument("--meaning-threshold", type=float, default=0.35, help="Within-binary_root threshold for meaning subclusters (requires gloss/definition).")
    ap.add_argument("--max-group", type=int, default=400, help="Skip similarity+subclustering for very large binary_root groups.")
    ap.add_argument("--qa-max-pairs", type=int, default=200, help="Max random pairs per group for QA coherence.")
    ap.add_argument("--qa-seed", type=int, default=1337, help="Seed for QA shuffle baseline.")
    ap.add_argument("--rebuild", action="store_true", help="Recompute clusters even if output already exists.")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Missing input: {args.input}")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    clusters_out = out_dir / "binary_root_lemma_clusters.jsonl"
    edges_out = out_dir / "binary_root_similarity_edges.csv"

    if not args.rebuild and clusters_out.exists() and edges_out.exists():
        print(f"[cache] Outputs already exist — skipping recompute. Use --rebuild to force.")
        print(f"  {clusters_out}")
        print(f"  {edges_out}")
        return

    groups: dict[str, list[LemmaRow]] = defaultdict(list)
    total_in = 0
    for rec in iter_jsonl(args.input):
        total_in += 1
        br = str(rec.get("binary_root") or "").strip()
        if not br:
            continue
        groups[br].append(
            LemmaRow(
                lemma=str(rec.get("lemma") or "").strip(),
                language=str(rec.get("language") or "").strip(),
                script=str(rec.get("script") or "").strip(),
                stage=str(rec.get("stage") or "").strip(),
                source=str(rec.get("source") or "").strip(),
                root_norm=str(rec.get("root_norm") or rec.get("root") or "").strip(),
                binary_root=br,
                translit=str(rec.get("translit") or "").strip(),
                ipa=str(rec.get("ipa") or rec.get("ipa_raw") or "").strip(),
                gloss=str(rec.get("gloss_plain") or rec.get("gloss") or rec.get("definition") or "").strip(),
            )
        )

    edge_fieldnames = ["binary_root", "src_lemma", "dst_lemma", "form_sim", "meaning_sim"]
    wrote_rows = 0
    wrote_edges = 0

    with clusters_out.open("w", encoding="utf-8") as out_f, edges_out.open("w", encoding="utf-8", newline="") as edges_f:
        edges_w = csv.DictWriter(edges_f, fieldnames=edge_fieldnames)
        edges_w.writeheader()

        for br, rows in sorted(groups.items(), key=lambda kv: (kv[0], len(kv[1]))):
            if not rows:
                continue
            if len(rows) > int(args.max_group):
                # emit rows without subclusters for huge groups (discovery safety)
                for r in rows:
                    out_f.write(
                        json.dumps(
                            {
                                "binary_root": br,
                                "lemma": r.lemma,
                                "root_norm": r.root_norm,
                                "form_cluster": None,
                                "meaning_cluster": None,
                                "language": r.language,
                                "stage": r.stage,
                                "script": r.script,
                                "source": r.source,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    wrote_rows += 1
                continue

            form_sim, meaning_sim = build_similarity(rows)
            form_clusters = cluster_indices(form_sim, threshold=float(args.form_threshold))
            meaning_clusters = cluster_indices(meaning_sim, threshold=float(args.meaning_threshold))

            # Emit per-lemma cluster assignments
            for idx, r in enumerate(rows):
                out_f.write(
                    json.dumps(
                        {
                            "binary_root": br,
                            "lemma": r.lemma,
                            "root_norm": r.root_norm,
                            "form_cluster": int(form_clusters[idx]),
                            "meaning_cluster": int(meaning_clusters[idx]),
                            "language": r.language,
                            "stage": r.stage,
                            "script": r.script,
                            "source": r.source,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                wrote_rows += 1

            # Emit similarity edges for inspection (all pairs)
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    edges_w.writerow(
                        {
                            "binary_root": br,
                            "src_lemma": rows[i].lemma,
                            "dst_lemma": rows[j].lemma,
                            "form_sim": f"{form_sim[i][j]:.6f}",
                            "meaning_sim": f"{meaning_sim[i][j]:.6f}",
                        }
                    )
                    wrote_edges += 1

    # QA coherence report (form/meaning) with shuffled baseline
    qa_dir = Path("outputs/qa")
    qa_dir.mkdir(parents=True, exist_ok=True)
    qa_path = qa_dir / "binary_root_coherence.json"

    # Build index map for QA
    all_rows: list[LemmaRow] = []
    idx_groups: dict[str, list[int]] = defaultdict(list)
    for br, rows in groups.items():
        for r in rows:
            idx = len(all_rows)
            all_rows.append(r)
            idx_groups[br].append(idx)

    form_feats = [char_ngrams(r.lemma, n=2) for r in all_rows]
    meaning_feats = [token_set(r.gloss) for r in all_rows]

    import random

    rng = random.Random(int(args.qa_seed))
    real_stats = avg_sim_for_groups(
        groups=idx_groups,
        form_feats=form_feats,
        meaning_feats=meaning_feats,
        max_pairs=int(args.qa_max_pairs),
        rng=rng,
    )
    shuf = shuffled_groups(idx_groups, rng=rng)
    shuf_stats = avg_sim_for_groups(
        groups=shuf,
        form_feats=form_feats,
        meaning_feats=meaning_feats,
        max_pairs=int(args.qa_max_pairs),
        rng=rng,
    )

    qa_payload = {
        "input": str(args.input),
        "rows_in": total_in,
        "binary_root_groups": len(groups),
        "qa_pairs": real_stats["pairs"],
        "form_avg": real_stats["form_avg"],
        "meaning_avg": real_stats["meaning_avg"],
        "baseline_form_avg": shuf_stats["form_avg"],
        "baseline_meaning_avg": shuf_stats["meaning_avg"],
        "seed": int(args.qa_seed),
        "max_pairs_per_group": int(args.qa_max_pairs),
    }
    qa_path.write_text(json.dumps(qa_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Read {total_in} rows, grouped into {len(groups)} binary_root buckets.")
    print(f"Wrote clusters: {clusters_out} (rows={wrote_rows})")
    print(f"Wrote edges:    {edges_out} (edges={wrote_edges})")
    print(f"Wrote QA:       {qa_path}")


if __name__ == "__main__":
    main()
