import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd
from scipy.sparse import hstack
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import silhouette_score
from sklearn.metrics import pairwise_distances_argmin_min

# Ensure Windows console prints Arabic without crashing
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def _resolve_text_column(df: pd.DataFrame, explicit: Optional[str]) -> str:
    """Pick a text column, preferring an explicit arg then common fallbacks."""
    if explicit:
        if explicit not in df.columns:
            raise ValueError(f"Text column '{explicit}' not found in data.")
        return explicit

    for candidate in ("text_ayah", "text_clean", "text"):
        if candidate in df.columns:
            return candidate
    raise ValueError(
        "No text column found. Expected one of: text_ayah, text_clean, text "
        "or pass --text-column."
    )


def load_data(path: str, text_column: Optional[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    col = _resolve_text_column(df, text_column)
    df = df.copy()
    df["__text__"] = df[col].astype(str)

    if "label" not in df.columns:
        if {"sura", "ayah"} <= set(df.columns):
            df["label"] = df["sura"].astype(str) + ":" + df["ayah"].astype(str)
        elif {"sura_no", "ayah_no"} <= set(df.columns):
            df["label"] = df["sura_no"].astype(str) + ":" + df["ayah_no"].astype(str)
        else:
            df["label"] = df.index.astype(str)
    return df


SIMPLE_AR_STOP = [
    "و",
    "في",
    "على",
    "من",
    "إلى",
    "الى",
    "عن",
    "ما",
    "لا",
    "لم",
    "لن",
    "إن",
    "أن",
    "هو",
    "هي",
    "هم",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "كان",
    "قد",
    "ثم",
    "كل",
]


def vectorize(texts: List[str], max_features: int, stop_words: Optional[Sequence[str]]) -> tuple[pd.DataFrame, CountVectorizer]:
    vectorizer = CountVectorizer(analyzer="word", max_features=max_features, stop_words=stop_words)
    X = vectorizer.fit_transform(texts)
    return X, vectorizer


def vectorize_roots(df: pd.DataFrame, root_cols: List[str], max_features: int, weight: float = 1.0):
    tokens = []
    for _, row in df.iterrows():
        parts = []
        for col in root_cols:
            if col in df.columns and pd.notna(row[col]) and str(row[col]).strip():
                parts.append(str(row[col]).strip())
        tokens.append(" ".join(parts))
    vectorizer = CountVectorizer(analyzer="word", max_features=max_features)
    X = vectorizer.fit_transform(tokens)
    if weight != 1.0:
        X = X.multiply(weight)
    return X, vectorizer


def cluster_texts(X, k: int) -> KMeans:
    model = KMeans(n_clusters=k, random_state=42, n_init="auto")
    model.fit(X)
    return model


def top_terms_by_labels(X, labels, vectorizer: CountVectorizer, top_n: int = 10):
    terms = vectorizer.get_feature_names_out()
    unique_labels = sorted(pd.unique(labels))
    for lbl in unique_labels:
        mask = labels == lbl
        if mask.sum() == 0:
            yield lbl, []
            continue
        mean_vec = X[mask].mean(axis=0).A1
        top_idx = mean_vec.argsort()[::-1][:top_n]
        yield lbl, [terms[i] for i in top_idx]


def summarize_clusters(df: pd.DataFrame, cluster_col: str, root_cols: List[str]) -> None:
    print("\n=== Cluster counts ===")
    print(df[cluster_col].value_counts().sort_index().to_string())

    for c in sorted(df[cluster_col].unique()):
        sub = df[df[cluster_col] == c]
        print(f"\n=== Cluster {c} samples ===")
        for _, row in sub.head(5).iterrows():
            snippet = row["__text__"][:120].replace("\n", " ")
            print(f"{row['label']}\t{snippet}")

    for root_col in root_cols:
        if root_col in df.columns:
            print(f"\n=== Top roots for {root_col} by cluster ===")
            for c in sorted(df[cluster_col].unique()):
                sub = df[df[cluster_col] == c]
                counts = sub[root_col].value_counts().head(5)
                print(f"\nCluster {c} ({root_col})")
                print(counts.to_string())


def cluster_report(df: pd.DataFrame, X_full, model: KMeans, text_vec: CountVectorizer, root_cols: List[str], X_text, top_n_terms=10):
    print("\n=== Cluster explain ===")
    labels = model.labels_
    # central ayah per cluster
    closest, _ = pairwise_distances_argmin_min(model.cluster_centers_, X_full)

    # top terms by labels
    term_lists = dict(top_terms_by_labels(X_text, labels, text_vec, top_n=top_n_terms))

    for idx in sorted(pd.unique(labels)):
        print(f"\n--- Cluster {idx} ---")
        term_line = ", ".join(term_lists.get(idx, []))
        print(f"Top terms: {term_line}")
        # top roots summary
        for root_col in root_cols:
            if root_col in df.columns:
                counts = df[df["cluster"] == idx][root_col].value_counts().head(5)
                if len(counts):
                    items = ", ".join([f"{k} ({v})" for k, v in counts.items()])
                    print(f"Top {root_col}: " + items)
        # central ayah
        center_idx = closest[idx]
        row = df.iloc[center_idx]
        snippet = row["__text__"][:200].replace("\n", " ")
        print(f"Central ayah: {row['label']} -> {snippet}")
        # 3 sample rows
        sample_rows = df[df["cluster"] == idx].head(3)
        for _, r in sample_rows.iterrows():
            s_snip = r["__text__"][:120].replace("\n", " ")
            print(f"Sample: {r['label']} -> {s_snip}")


def plot_clusters(df: pd.DataFrame, X, cluster_col: str, out_path: str, pca_csv: Optional[str] = None):
    coords = PCA(n_components=2, random_state=42).fit_transform(X.toarray())
    df = df.copy()
    df["pca_x"], df["pca_y"] = coords[:, 0], coords[:, 1]

    if pca_csv:
        Path(pca_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(pca_csv, index=False)
        print(f"[saved] {pca_csv}")

    max_points = 400
    max_labels = 150
    if len(df) > max_points:
        df_plot = df.sample(n=max_points, random_state=42)
        print(f"[info] Plotting {max_points} sampled points out of {len(df)} for readability.")
    else:
        df_plot = df

    plt.figure(figsize=(8, 6))
    cmap = plt.colormaps.get_cmap("tab10")
    unique_clusters = sorted(df_plot[cluster_col].unique())
    color_map = {c: cmap(i % cmap.N) for i, c in enumerate(unique_clusters)}

    for idx, (i, row) in enumerate(df_plot.iterrows()):
        c = int(row[cluster_col])
        plt.scatter(row["pca_x"], row["pca_y"], color=color_map[c], s=70, alpha=0.8)
        if idx < max_labels:
            plt.text(row["pca_x"] + 0.02, row["pca_y"] + 0.02, row["label"], fontsize=8)

    plt.title("Co-occurrence cluster map (PCA)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[saved] {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Level 1 co-occurrence clustering for Quran text/root samples."
    )
    parser.add_argument(
        "--input",
        default=os.path.join("..", "Resources", "examples_rj.csv"),
        help="Path to CSV with columns text_ayah (or text_clean/text).",
    )
    parser.add_argument("--text-column", help="Override text column name.")
    parser.add_argument("--k", type=int, default=2, help="Number of clusters (KMeans).")
    parser.add_argument(
        "--auto-k",
        help="Optional comma-separated ks to choose best silhouette; overrides --k if provided.",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=5000,
        help="Max vocabulary size for CountVectorizer.",
    )
    parser.add_argument(
        "--max-root-features",
        type=int,
        default=200,
        help="Max vocabulary size for root features when --use-roots is on.",
    )
    parser.add_argument(
        "--root-weight",
        type=float,
        default=1.0,
        help="Multiplier for root feature counts when --use-roots is on.",
    )
    parser.add_argument(
        "--out-csv",
        default=os.path.join("output", "cluster_assignments.csv"),
        help="Where to write cluster assignments.",
    )
    parser.add_argument(
        "--plot",
        default=os.path.join("output", "cluster_plot.png"),
        help="Path to save PCA scatter plot (set empty to skip).",
    )
    parser.add_argument(
        "--pca-csv",
        default="",
        help="Optional path to save full PCA coordinates CSV (with cluster labels).",
    )
    parser.add_argument(
        "--use-roots",
        action="store_true",
        help="Augment features with root2/root3/root token counts.",
    )
    parser.add_argument(
        "--k-compare",
        default=None,
        help="Optional comma-separated ks to compare via silhouette (e.g., 2,3,4).",
    )
    parser.add_argument(
        "--stop-words",
        default="simple",
        choices=["none", "simple"],
        help="Stop-word list for text vectorizer.",
    )
    parser.add_argument(
        "--meta-json",
        default=os.path.join("output", "run_metadata.json"),
        help="Path to write run metadata JSON.",
    )
    args = parser.parse_args()

    df = load_data(args.input, args.text_column)

    print(f"[info] Loaded {len(df)} rows from {args.input}")
    stop_words = None if args.stop_words == "none" else SIMPLE_AR_STOP
    X_text, vec_text = vectorize(df["__text__"].tolist(), args.max_features, stop_words=stop_words)
    root_cols = ["root2", "root3", "root"]
    X = X_text
    vec_roots = None
    root_vocab = None
    if args.use_roots:
        X_root, vec_roots = vectorize_roots(df, root_cols, args.max_root_features, weight=args.root_weight)
        X = hstack([X_text, X_root])
        root_vocab = vec_roots.get_feature_names_out().shape[0]
        print(
            f"[info] Using roots. Text feat: {X_text.shape[1]}, Root feat: {X_root.shape[1]}, weight={args.root_weight}"
        )

    # Optional k comparison
    silhouette_scores = {}
    k_for_run = args.k
    def maybe_eval_ks(ks_list: List[int]):
        scored = {}
        for k_val in ks_list:
            if k_val < 2 or k_val >= len(df):
                print(f"k={k_val}: skipped (invalid for silhouette)")
                continue
            m_tmp = cluster_texts(X, k_val)
            score = silhouette_score(X, m_tmp.labels_) if len(df) > k_val else float("nan")
            scored[k_val] = score
            print(f"k={k_val}: silhouette={score:.4f}")
        return scored

    if args.k_compare:
        try:
            ks = [int(x.strip()) for x in args.k_compare.split(",") if x.strip()]
            print("\n=== k comparison (silhouette) ===")
            silhouette_scores.update(maybe_eval_ks(ks))
        except Exception as e:
            print(f"[warn] k-compare failed: {e}")

    if args.auto_k:
        try:
            ks_auto = [int(x.strip()) for x in args.auto_k.split(",") if x.strip()]
            print("\n=== auto-k (silhouette choose best) ===")
            scores = maybe_eval_ks(ks_auto)
            if scores:
                best_k = max(scores.items(), key=lambda kv: kv[1])[0]
                k_for_run = best_k
                silhouette_scores.update(scores)
                print(f"[info] auto-k selected k={best_k}")
        except Exception as e:
            print(f"[warn] auto-k failed: {e}")

    model = cluster_texts(X, k_for_run)
    df["cluster"] = model.labels_

    summarize_clusters(df, "cluster", root_cols=root_cols)

    print("\n=== Top terms per cluster ===")
    for c_idx, terms in top_terms_by_labels(X_text, model.labels_, vec_text, top_n=10):
        print(f"Cluster {c_idx}: {', '.join(terms)}")

    cluster_report(df, X, model, vec_text, root_cols=root_cols, X_text=X_text, top_n_terms=10)

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    df_out = df.drop(columns=["__text__"])
    df_out.to_csv(args.out_csv, index=False)
    print(f"[saved] {args.out_csv}")

    if args.plot:
        plot_clusters(df, X, "cluster", args.plot, pca_csv=args.pca_csv or None)
    else:
        print("[skip] plot disabled")

    meta = {
        "input": args.input,
        "rows": len(df),
        "k": k_for_run,
        "k_compare": args.k_compare,
        "auto_k": args.auto_k,
        "use_roots": args.use_roots,
        "text_vocab": int(X_text.shape[1]),
        "timestamp": datetime.now(tz=datetime.now().astimezone().tzinfo).isoformat(),
        "max_features": args.max_features,
        "max_root_features": args.max_root_features,
        "out_csv": args.out_csv,
        "plot": args.plot,
        "stop_words": args.stop_words,
        "root_weight": args.root_weight,
    }
    try:
        if args.use_roots:
            meta["root_vocab"] = int(root_vocab) if root_vocab is not None else None
        if silhouette_scores:
            meta["silhouette_scores"] = silhouette_scores
        os.makedirs(os.path.dirname(args.meta_json), exist_ok=True)
        Path(args.meta_json).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[saved] {args.meta_json}")
    except Exception as e:
        print(f"[warn] could not write metadata: {e}")


if __name__ == "__main__":
    main()
