Root قتل clustering run (Level 1)
=================================

Data preparation
- Source root map: `Resources/word_root_map.csv` built from `Resources/qac_morphology/quran-morphology.txt`.
- Extracted verses for root قتل (dedup per sura/ayah): `Quran-s-Words-decoding-LV1/Codex CLI/output/examples_ktl.csv` (114 rows).
  - Text column from `Resources/quran_dataset including CSV/quran_text.csv` (text_with_diacritics).

Clustering settings (`01_rj_cooc.py`)
- Input: `examples_ktl.csv`
- Features: bag-of-words with simple Arabic stop-list; root features on.
- Root weighting: 1.5
- Auto-k: silhouette over k = 2,3,4 → chose k = 2 (scores: {2: 0.2399, 3: 0.1576, 4: 0.1442})
- PCA saved to `examples_ktl_pca.csv`; plot to `examples_ktl_plot.png`
- Assignments saved to `examples_ktl_clusters.csv`; metadata `examples_ktl_meta.json`

Results
- Cluster counts: k=2 → {0: 78, 1: 36}
- Cluster 0
  - Central ayah: 3:169 — وَلَا تَحْسَبَنَّ ٱلَّذِينَ قُتِلُوا۟ فِى سَبِيلِ ٱللَّهِ أَمْوَٰتًۢا ...
  - Sample ayat: 2:54, 2:72, 2:87
  - Top terms: ٱل, ٱلل, ون, ين, وا, وه, يل, ال, وك, ان
- Cluster 1
  - Central ayah: 6:151 — ... وَلَا تَقْتُلُوٓا۟ أَوْلَٰدَكُم مِّنْ إِمْلَٰقٍۢ ...
  - Sample ayat: 2:61, 2:85, 2:191
  - Top terms: ٱل, وا, ٱلل, ون, ين, ال, يل, ام, وه, اب

Key files
- Input: `Quran-s-Words-decoding-LV1/Codex CLI/output/examples_ktl.csv`
- Clusters: `.../examples_ktl_clusters.csv`
- Plot: `.../examples_ktl_plot.png`
- PCA coords: `.../examples_ktl_pca.csv`
- Metadata: `.../examples_ktl_meta.json`
