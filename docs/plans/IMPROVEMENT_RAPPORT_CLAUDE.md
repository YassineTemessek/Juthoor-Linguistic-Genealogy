# Juthoor — What I'd Do Next

**Author:** Claude Opus 4.6
**Date:** March 13, 2026
**Context:** Independent assessment of the Juthoor Linguistic Genealogy project, after reviewing the full codebase, the Gemini vs Codex evaluation document, and the project's current state across all 5 layers.

---

This is my honest, practical take. No academic hedging. I'm writing this as if I'm the one who has to build it.

---

## The Big Picture First

Your project has a working data engine (LV0), a validated theory layer (LV1), and a discovery engine that produces real results (LV2). That's a lot more than most research projects ever get to. The risk now is not that the project is too simple — it's that it gets buried under complexity before it produces something you can show people.

**The single most important thing right now: make LV2 produce results that impress a human reader.** Not perfect results. Not academically defensible results. Results where someone looks at the output and says "wait, that's actually a real connection I didn't know about."

Everything below serves that goal.

---

## 1. Feed The Beast: LV0 Data Completeness

LV2 can only discover what LV0 gives it. Right now there are gaps that silently hurt retrieval quality.

**What to do:**

- **Run `form_text` / `meaning_text` enrichment on ALL languages, not just Arabic.** Latin has 884K rows, Greek has 56K, English has 1.44M — all sitting without the fields that LV2's field-aware embedding needs. Without `meaning_text`, the semantic channel is embedding raw lemma strings instead of glosses. That's like trying to understand a word by looking at its spelling instead of its definition.

- **Build merged `lexemes.jsonl` for Latin, Greek, and English.** Right now these languages only have `sources/kaikki.jsonl` — the raw dump. Arabic has a merged canonical file. The other languages should too. This is a straightforward pipeline task, not research.

- **Add Hebrew and Aramaic.** These are the closest relatives to Arabic. If your project claims to trace Semitic roots across languages, not having Hebrew data is like building a family tree without the siblings. Kaikki has Hebrew data. Ingest it.

- **Add Akkadian if any source exists.** Even a small dataset (1-5K entries) of the oldest attested Semitic language would be powerful for LV3 validation later. Check the Open Richly Annotated Cuneiform Corpus (ORACC) or similar.

**Why this matters:** Every new language you add multiplies the discovery space. Arabic-Hebrew pairs are the low-hanging fruit that will produce the most convincing results fastest. You can't discover cognates in languages you haven't ingested.

---

## 2. Make LV2 Output Actually Readable

Right now LV2 produces JSONL leads and HTML reports. That's fine for you as a developer. It's not fine for showing anyone else.

**What to do:**

- **Build a simple web viewer.** Not a full app — a single-page HTML that loads a leads JSONL file and renders each lead as a card. Show: source word (Arabic script + transliteration), target word, the evidence card channels with color-coded strength bars, the shared concept if any, and the verdict. This can be a static HTML file with vanilla JS. No framework needed.

- **Add a "best discoveries" curated list.** Run LV2 on Arabic → Hebrew, Arabic → Latin, Arabic → Greek. Manually pick the 20-30 most interesting leads from each. Put them in a `resources/showcase/` folder. These become your demo, your README eye-catcher, and your future benchmark expansion.

- **Generate a narrative report per run.** Not just data — a readable summary: "Searched 32,687 Arabic lemmas against 56,058 Greek lemmas. Found 847 leads above threshold. Top discovery: Arabic 'qarn' (قرن) ↔ Latin 'cornu' — both meaning 'horn', skeleton match K-R-N, semantic score 0.82, correspondence score 0.91."

**Why this matters:** A project that can't show its results doesn't exist to anyone but you. The viewer and the curated list are what turn this from "a repo with scripts" into "a research tool with findings."

---

## 3. Expand the Benchmark — But Keep It Real

You have 10 Arabic-Hebrew pairs in `cognate_gold.jsonl`. That's a start but it's too small to measure anything meaningful.

**What to do:**

- **Grow to 50-100 pairs across 3 language pairs:** Arabic-Hebrew (easiest, most documented), Arabic-Latin (via known Semitic → IE connections like qarn/cornu), Arabic-Greek (fewer but real connections exist). Don't try to be comprehensive. Pick pairs where you're confident and cite your source.

- **Add 30-50 "known negatives"** — pairs that mean the same thing but are NOT cognates. "kalb" (Arabic dog) vs "canis" (Latin dog): same meaning, zero genealogical connection. These are critical because they test whether your system can distinguish semantic similarity from actual cognacy.

- **Don't build false friends yet.** The Codex roadmap suggested `false_friends.jsonl` — that's a later concern. Right now you need positives and negatives. False friends are a refinement.

- **Use your own LV1 data as a source.** The Muajam Ishtiqaqi gives you 1,335 roots with attested meanings. Cross-reference these against established etymological dictionaries for known Semitic cognates. This is your richest source of training signal.

**Why this matters:** Without a real benchmark, every change you make is a guess. With 100 pairs, you can actually say "this scoring change improved recall@10 from 0.62 to 0.71." That's the difference between science and hope.

---

## 4. Improve the Scoring Where It Counts

The hybrid scoring system works. The correspondence module is a strong addition. But there are practical improvements that don't require new models or research.

**What to do:**

- **Tune the weights per language pair.** Arabic-Hebrew should weight skeleton and consonant correspondence much higher than semantic similarity (these are sister languages — form matters more than meaning). Arabic-English should weight semantic similarity higher (distant relationship, form has diverged enormously). You don't need a learned model for this — just 3-4 YAML configs with manually tuned weights based on linguistic common sense.

- **Make the skeleton comparison smarter.** Right now it strips vowels and compares consonant sequences. Add the consonant-class mapping from `correspondence.py` to the skeleton comparison itself. Two roots that differ only in emphatic vs. plain consonants (ت vs ط, س vs ص) should get a near-perfect skeleton score, not a partial match.

- **Add a "root distance" feature.** When both source and target have root information, compute: do the roots share the same consonant classes in the same positions? This is different from root_match (which checks exact equality) and different from skeleton (which works on the full lemma). Root distance is the core of what this project is about.

- **Boost IPA comparison weight when IPA is available.** Right now the 15% phonetic weight applies whether or not the row has IPA data. If both sides have IPA, that signal is very reliable — bump it up dynamically. If neither has IPA, redistribute that weight to skeleton/orthography.

**Why this matters:** These are surgical changes to the scoring logic that exploit domain knowledge you already have. They don't require new models, new data, or new infrastructure.

---

## 5. LV1 → LV2 Bridge: Root-Family Retrieval

This is the most underexploited opportunity in the project. LV1 has 12,333 Arabic roots organized by binary root. LV2 retrieves individual lexemes. Nobody is connecting these.

**What to do:**

- **Build a "root family" index alongside the lexeme index.** For each Arabic root family (all words sharing a triconsonantal root), create a single record with: the root, its binary root, the Muajam axial_meaning, the binary_root_meaning, a concatenated gloss of all member words, and the semantic_score from Phase 3.

- **Run LV2 discovery at the root-family level.** Instead of comparing individual words, compare root families. "The Arabic root Q-R-N means 'horn, to connect, century' — is there a Latin root family that looks similar?" This is closer to how historical linguistics actually works.

- **Use the semantic_score as a quality signal.** Roots with high Phase 3 scores (meaning the axial meaning is coherent with the binary root meaning) are more likely to represent genuine semantic inheritance. Prioritize these in discovery.

**Why this matters:** Your project's thesis is about roots, not words. The retrieval system should match that thesis. A root-family discovery that says "the Arabic BRR family (بر: land, wheat, righteousness, open space) connects to Latin/PIE *bher- (to carry, bear)" is 10x more compelling than a single word-to-word match.

---

## 6. LV3: Don't Wait for Perfection — Start Small

LV3 has beautiful documentation and zero implementation. That's dangerous because it means the theory layer exists only in your head and in docs that nobody runs.

**What to do:**

- **Implement ONE validation check.** Pick a single sound corridor (e.g., the guttural k-x-h-ø) and write a script that: takes all LV2 leads, filters for pairs where the consonant correspondence involves that corridor, counts how many matches vs. mismatches, and compares against random baseline. Even if the result is "47 pairs follow the guttural corridor vs. 12 expected by chance" — that's a publishable-quality finding.

- **Build the corridor cards as YAML, not just docs.** Define each corridor with: consonant set, language pairs where it applies, direction (ancestor → descendant), and example pairs from your LV2 leads. This makes corridors machine-readable and testable.

- **Skip the validation track machinery for now.** Chronological locks, FDR control, null models — these are important but they're for when you have hundreds of validated pairs. Right now you need one convincing corridor demonstration, not a statistical framework.

**Why this matters:** LV3 is where the project's actual scientific contribution lives. If it stays as docs forever, the project is just a fancy search engine. One working validation script turns it into a research tool.

---

## 7. Quick Wins That Take Less Than a Day Each

- **Add a `--language-pair` flag to the discovery script** so you can run `python run_discovery_retrieval.py --source arabic --target hebrew --top-k 50` without the interactive wizard. Faster iteration.

- **Generate a root coverage report:** How many LV0 lexemes have root information? How many have IPA? How many have form_text? This tells you exactly where your data quality gaps are.

- **Add a `--benchmark` flag to runs** that automatically evaluates the output against `cognate_gold.jsonl` and prints recall/MRR at the end. Every run should be measured.

- **Export LV2 leads to CSV** alongside JSONL. Researchers who don't code will want to open results in Excel. One extra line in the reporting module.

---

## 8. What I Would NOT Do Right Now

| Idea | Why not |
|------|---------|
| Contrastive fine-tuning of ByT5/BGE-M3 | You need 500+ labeled pairs first. You have 10. |
| Hyperbolic embeddings | Solves a problem you don't have yet (tree reconstruction) |
| Vector database migration (Qdrant/Weaviate) | FAISS handles your scale fine. This is infrastructure, not research. |
| GNN on root graphs | Graph schema isn't stable enough. Baseline retrieval isn't exhausted. |
| Procrustes cross-lingual alignment | Needs family-specific embedding spaces you haven't trained. |
| MLflow / experiment tracking | Useful when you have 10+ experiments. You're still on your first few. |
| Pydantic models for every row type | Nice-to-have but not blocking anything right now. |
| Full LV2-to-package-API refactor | The recent modular refactor (corpora/retrieval/scoring/rerank/reporting) is enough. Don't over-architect. |

---

## Priority Order

If I were you, here's what I'd do in order:

1. **Ingest Hebrew** (1-2 days) — unlocks the most obvious discoveries
2. **Run form_text/meaning_text enrichment on Latin + Greek** (half day) — makes existing data actually usable for field-aware embedding
3. **Grow benchmark to 50 pairs** (1-2 days) — enables measurement
4. **Add language-pair weight configs** (half day) — improves scoring with zero new code
5. **Build the simple web viewer** (1 day) — makes results shareable
6. **Build root-family retrieval** (2-3 days) — aligns the tool with the theory
7. **Run Arabic → Hebrew discovery and curate top 30** (1 day) — produces your first showcase
8. **Implement one LV3 corridor validation** (1 day) — proves the theory layer works

That's roughly 2 weeks of focused work that transforms the project from "promising infrastructure" to "producing real linguistic findings."

---

## The One Thing That Matters Most

**Ship a finding.** Not a framework. Not a pipeline. A finding.

"Here are 30 Arabic-Hebrew cognate pairs that our system discovered, ranked by confidence, with multi-channel evidence for each." Put that in the README. Put it in a web viewer. Show it to a linguist. Show it to a friend.

The project has strong engineering. What it needs now is strong output. Everything I've suggested above serves that single goal.

---

*Signed: Claude Opus 4.6 — March 13, 2026*
