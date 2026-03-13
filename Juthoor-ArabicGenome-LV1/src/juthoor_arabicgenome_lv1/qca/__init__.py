"""
juthoor_arabicgenome_lv1.qca
============================
Quranic Corpus Analysis (QCA) — integrated into LV1 (ArabicGenome).

Focuses on word-level relationships within the Quran: root co-occurrence
clustering, semantic distance, and nuance between closely related words.
Consumes LV0 canonical outputs (QAC morphology, Quran text CSV) and
produces annotated CSV outputs for human review.

Analysis scripts live in scripts/qca/:
- build_word_root_map.py  -- parse QAC morphology -> word/root CSV
- make_examples_from_roots.py -- extract verses by root set
- make_subset.py          -- extract verses by substring patterns
- 01_rj_cooc.py           -- KMeans co-occurrence clustering + PCA plot
"""

__version__ = "0.1.0"
__all__: list[str] = []
