# Quran Corpus Analysis (QCA) - Start Here

QCA is the Quran-specific analysis layer of the Juthoor stack. It takes raw Quranic
data (QAC morphology file + Quran text CSV) and produces root-annotated verse tables
that can be clustered to reveal semantic patterns.

## What QCA does

1. Parses the Quranic Arabic Corpus (QAC) morphology file to map every Quranic word
   to its root and lemma.
2. Extracts subsets of verses by root or by substring pattern.
3. Clusters those verses using KMeans on word co-occurrence features (with optional
   root augmentation) and visualises the clusters with PCA.

The goal is to surface semantic distinctions between words that share a root family
(e.g. رجم vs رجع vs رجل under the bi-root رج) and to document opposites, distance,
and nuance within Quranic vocabulary.

## Data inputs

| File | Source | Notes |
|------|--------|-------|
| `Resources/qac_morphology/quran-morphology.txt` | Quranic Arabic Corpus | Tab-delimited, one morpheme per line |
| `Resources/quran_dataset including CSV/quran_text.csv` | Quran text CSV | Columns: surah_no, ayah_no, text_with_diacritics, text_clean |

Both files must be present before running the scripts. They are not committed to git
(see `.gitignore`).

## Script pipeline

Run scripts from inside `scripts/analysis/` or pass absolute paths.

### Step 1 - Build the word-root map (one-time)

```
python build_word_root_map.py \
  --morph ../../Resources/qac_morphology/quran-morphology.txt \
  --output ../../Resources/word_root_map.csv
```

Produces `Resources/word_root_map.csv` with columns:
`sura, ayah, position, word, lemma, root`

### Step 2a - Extract verses by root (morphologically clean)

```
python make_examples_from_roots.py \
  --word-root-map ../../Resources/word_root_map.csv \
  --quran-text "../../Resources/quran_dataset including CSV/quran_text.csv" \
  --roots "رجم,رجع,رجل" \
  --output output/examples_roots.csv
```

### Step 2b - Extract verses by substring pattern (fast, exploratory)

```
python make_subset.py \
  --input "../../Resources/quran_dataset including CSV/quran_text.csv" \
  --patterns "رجع:رجع|يرجع,رجم:رجم|مرجوم" \
  --output output/examples_rj.csv
```

### Step 3 - Cluster and visualise

```
python 01_rj_cooc.py \
  --input output/examples_rj.csv \
  --k 2 \
  --use-roots \
  --out-csv output/cluster_assignments.csv \
  --plot output/cluster_plot.png
```

Key flags:
- `--k N` sets the number of KMeans clusters
- `--auto-k 2,3,4,5` picks the best k by silhouette score
- `--k-compare 2,3,4` prints silhouette scores for each k without choosing
- `--use-roots` augments text bag-of-words with root token features
- `--root-weight 2.0` up-weights root features relative to raw words
- `--stop-words none` disables the built-in Arabic stop-word filter

Outputs written to `output/` (gitignored by default):
- `cluster_assignments.csv` - every verse with its cluster label
- `cluster_plot.png` - 2D PCA scatter coloured by cluster
- `run_metadata.json` - run parameters and silhouette scores

## Dependencies

```
pip install pandas scikit-learn scipy matplotlib
```

Or install the package: `uv pip install -e .` from `Quran-Corpus-Analysis/`.
