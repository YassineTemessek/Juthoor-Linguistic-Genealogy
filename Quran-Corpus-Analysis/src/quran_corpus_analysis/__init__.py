"""
quran_corpus_analysis
=====================
Quranic semantic analysis layer (QCA).

Focuses on word-level relationships within the Quran: root co-occurrence
clustering, semantic distance, and nuance between closely related words.
Consumes LV0 canonical outputs (QAC morphology, Quran text CSV) and
produces annotated CSV outputs for human review.

Active analysis scripts live in scripts/analysis/:
- build_word_root_map.py  -- parse QAC morphology -> word/root CSV
- make_examples_from_roots.py -- extract verses by root set
- make_subset.py          -- extract verses by substring patterns
- 01_rj_cooc.py           -- KMeans co-occurrence clustering + PCA plot
"""

__version__ = "0.1.0"
__all__: list[str] = []
