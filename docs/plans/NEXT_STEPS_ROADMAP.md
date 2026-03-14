# Juthoor — Next Steps Roadmap
**After LV1 Research Factory completion (baseline: deda74b, 2026-03-14)**

---

## Three lanes, prioritized

### Lane 1: LV0 Data Gaps (NEXT — immediate)
Audit which languages are missing or incomplete in the data core.
Key targets: Hebrew, Aramaic/Syriac, Akkadian, Amharic — the Semitic family.
Also: any Indo-European gaps needed for LV2 corridor experiments.
Codex handles heavy ingestion work.

### Lane 2: LV2 Genome-Informed Discovery (NEXT — after Lane 1)
Wire LV1's promoted outputs into LV2's retrieval/scoring pipeline:
- Field coherence scores → weight cognate candidates by root family coherence
- Positional profiles → position-aware cross-lingual matching
- Metathesis pairs → detect metathesized cognates across languages
Goal: measure whether genome-informed discovery finds better cognates than blind discovery.

### Lane 3: LV3 Theory Bootstrap (FUTURE — parked)
LV3 has architecture docs but zero code. The evidence cards from LV1 are the first real inputs:
- Build the evidence ingestion pipeline
- Create the first "corridor" models (language family connections)
- Start formalizing genealogical hypotheses with LV1 data as backing
This is the most ambitious lane. Parked until LV0+LV2 are solid.

---

*Last updated: 2026-03-14*
