Gemini:

  Responding with gemini-3-flash-preview
✦ The Juthoor Linguistic Genealogy project is a sophisticated, multi-layered linguistic engine designed to trace the "DNA" of human language, primarily through the
  Arabo-Semitic root system. It operates as a Python workspace using uv, where each layer (LV0–LV3) builds upon the data and logic of the one below it.


  1. The Foundation: Data Ingestion (LV0 - DataCore)
  The system starts with Juthoor-DataCore-LV0, which serves as the "single source of truth."
   * Canonical Pipeline: It ingests raw data from diverse sources (Wiktionary dumps via Kaikki.org, the Quranic Arabic Corpus, and classical dictionaries) and normalizes
     them into a unified JSONL lexeme schema.
   * Enrichment: Every entry is enriched with phonetic (IPA), orthographic (raw script), and transliterated fields. A specific build_text_fields step ensures that lemmas
     are optimized for both machine processing and human readability.


  2. The Core Logic: Arabic Genome & Discovery (LV1 & LV2)
   * LV1 (Arabic Genome): This layer focuses on decoding the biconsonantal (2-letter) root system. It attempts to map the "atomic" meanings of specific sound combinations
     in Arabic.
   * LV2 (Discovery Engine): This is the project's analytical powerhouse. It uses a Hybrid Scoring mechanism to find potential cognates across language families (e.g.,
     comparing Arabic to Latin or English).
       * Semantic View: Uses SONAR and BGE-M3 embeddings to find "meaning neighbors" in a shared vector space.
       * Form View: Uses CANINE (a character-level model) and custom Skeleton Similarity (comparing consonantal sequences while ignoring vowels) to find sound/spelling
         neighbors.
       * Composite Scoring: Scores are weighted: Semantics (~40%), Form (~20%), Orthography (15%), Sound (15%), and Skeleton (10%), with a boost for same-family languages.


  3. Theory & Synthesis (LV3 - Origins)
  Juthoor-Origins-LV3 moves from discovery to historical hypothesis testing.
   * Lemma Anchors: To bridge families, it uses Latin as a "cross-family pivot." Every concept (like "WATER" or "EYE") is anchored to a verified Latin lemma (e.g., aqua,
     oculus).
   * Discovery Corridors: It tracks "sound corridors" (e.g., the k-x-h-Ø guttural corridor) as soft tags during discovery, allowing the system to suggest connections that
     follow known phonetic shifts.
   * Validation Track: The project maintains a "discovery-first" mode (high recall) but is designed to transition to a strict "validation track" that enforces chronological
     locks and rigid phonetic laws.


  4. Technical Stack
   * Language: Python 3.11+ (Workspace structure).
   * AI/ML: PyTorch, Hugging Face Transformers (CANINE/ByT5), and FlagEmbedding (BGE-M3).
   * Vector Search: FAISS for high-speed similarity retrieval.
   * Data Architecture: Heavily focused on JSONL for streamable, scalable data processing, with exports designed for Neo4j graph visualization.


  This architecture allows the project to scale from raw dictionary scraping to complex AI-driven genealogical mapping of linguistic roots across thousands of years.

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
 > any technical aspect you suggest to upgrade or change? for example the embeding techiniques?
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  Responding with gemini-3-flash-preview
✦ Based on the current architecture and the specific goals of tracing linguistic genealogy (which is different from standard semantic search), here are several technical
  upgrades and changes I would suggest, particularly regarding the embedding techniques and the data pipeline:


  1. Transition to "Cognate-Aware" Contrastive Learning
  Currently, you use BGE-M3 and SONAR, which are optimized for semantic similarity (synonyms). However, genealogy requires genealogical similarity (cognates).
   * The Problem: BGE-M3 might give a high score to "Dog" (English) and "Kalb" (Arabic for 'dog') because they mean the same thing, even though they are etymologically
     unrelated. It might give a low score to "Horn" (English) and "Qarn" (Arabic), which are likely cognates but have different semantic nuances in modern contexts.
   * The Upgrade: Use a Triplet Loss or Contrastive Learning approach to fine-tune your ByT5/CANINE models using your "Gold" anchor pairs. This would train the embedding
     space to ignore "noise" (vowel shifts) and focus on "signal" (consonantal correspondences) specific to the sound corridors you've identified.


  2. Hyperbolic Embeddings for Hierarchical Data
  Language genealogy is inherently tree-like (hierarchical).
   * The Problem: Standard Euclidean embeddings (like those used in FAISS or BGE-M3) struggle to represent hierarchical structures accurately without high distortion.
   * The Upgrade: Explore Poincaré Embeddings (Hyperbolic space). These are mathematically optimized to represent hierarchies. In a hyperbolic embedding space, the
     "distance" between nodes grows exponentially as you move toward the leaves, which perfectly mirrors the divergence of languages from a common root (the "Origin").


  3. Cross-Lingual Mapping (Procrustes Alignment)
  Instead of relying on a single multilingual model like SONAR, which is a "black box," you could align language-specific spaces.
   * The Upgrade: Train high-quality embeddings for Arabic/Semitic and Indo-European languages separately on historical corpora, then use Orthogonal Procrustes Alignment to
     map them into a shared space using your 536 "Anchor Concepts" as the transformation matrix. This preserves the internal linguistic relationships of each family better
     than a generic multilingual model.


  4. Integration of Graph Neural Networks (GNNs)
  Your LV1 and LV2 data is essentially a graph (Roots → Lemmas → Cognates).
   * The Upgrade: Implement a GraphSAGE or GAT (Graph Attention Network) layer over your Neo4j exports. Instead of comparing two isolated words, a GNN can produce an
     embedding for a word based on its context in the root graph (e.g., what other words share this biconsonantal root?). This would allow LV3 to "see" that two words are
     related because their "root neighborhoods" look similar.


  5. Shift to a Vector Database (Scalability)
  As you move from 500 concepts to 10,000+ lemmas across 20+ languages, managing static FAISS files will become cumbersome.
   * The Upgrade: Integrate a vector database like Qdrant or Weaviate. These support "Hybrid Search" natively—allowing you to combine vector similarity (embeddings) with
     metadata filtering (e.g., lemma_status == 'gold') and keyword matching in a single query.


  6. Dynamic "Sound Corridor" Weighting
   * The Upgrade: Instead of a static 10% weight for the "Skeleton" score, you could use an Attention Mechanism that learns which component (Orthography vs. Sound vs.
     Skeleton) is most reliable for specific language pairs. For example, when comparing Maltese and Arabic, Orthography might get more weight; when comparing Hittite and
     Arabic, the Skeleton/IPA might be prioritized.


  Would you like me to investigate any of these specifically? I can use the newly installed context7 extension to pull the latest implementation patterns for things like
  Hyperbolic Embeddings or Contrastive Learning for NLP.

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
 > i shared your answer with openai codex and here what he answered what do you think: A lot of that is strong. The best parts of Gemini’s answer are the ones that match
   the actual failure mode of this repo: semantic similarity is not the same as genealogical relatedness.

   My view is:

   Mostly right

   Cognate-aware contrastive learning
   This is the strongest suggestion in that list.
   The current stack is still too semantic-first. For this project, a model trained to separate:

   cognates
   non-cognate translations
   borrowings
   false friends
   would be more valuable than swapping generic embedding models.
   I agree with the direction, with one caveat: don’t start with full end-to-end fine-tuning immediately. First build a labeled benchmark and a simple learned reranker. If
   that works, then move to contrastive fine-tuning.
   Dynamic weighting
   Also strong.
   Static weights in [hybrid_scoring.py](C:\Users\yassi\AI
   Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) are a bootstrap mechanism, not a
   final method.
   Different language pairs need different evidence weights. Arabic-Hebrew is not Arabic-English, and neither is Arabic-Latin.
   I would implement this first as:

   language-pair-specific calibrated models
   then maybe attention/gating later
   An explicit learned scorer is simpler and easier to debug than adding attention too early.
   GNNs
   Directionally good, but later-stage.
   If LV1/LV2 graphs become central objects, graph-based representation learning could help. But I would not do this before:

   the node/edge schema is stable
   you have a gold benchmark
   the non-graph baseline is already strong
   Otherwise you’ll add complexity without knowing if the gain is real.
   Promising but not first priority
   4. Procrustes alignment
   This is intellectually plausible and more transparent than relying only on a generic multilingual model.
   But it depends on having:

   solid language-specific spaces
   enough reliable anchors
   a clean shared concept inventory
   If your anchor concepts are good, this could be excellent for experiments. I still wouldn’t make it the first big investment because it’s research-heavy and sensitive
   to anchor quality.
   Vector database
   Reasonable eventually, but not urgent.
   For the current scale, FAISS files are fine. A vector DB helps when you need:
   serving
   filtering-heavy workflows
   concurrent querying
   persistent operational infrastructure
   Right now the bigger issue is retrieval quality, not storage technology.
   I would keep FAISS until the data/model pipeline stabilizes.
   Interesting, but I would push back
   6. Hyperbolic embeddings
   This is the weakest recommendation in practical terms.
   The theory makes sense because genealogy is hierarchical, but your actual task is not just tree reconstruction. It is a messy mix of:

   inheritance
   borrowing
   semantic drift
   root-pattern morphology
   partial correspondences across families
   That structure is not a clean tree. It is more like a graph with competing signals.
   Hyperbolic embeddings may become useful at LV3 for lineage modeling, but they are not where I would spend time for LV2 retrieval. They are likely too far downstream
   from your main bottleneck.
   Where I agree most strongly with Gemini
   The core insight is this:

   semantic similarity != cognate similarity

   That is exactly right, and it is the main technical limitation of using generic multilingual embeddings as the dominant signal.

   What I would change in Gemini’s plan
   I’d reorder it like this:

   Build a gold evaluation set.
   Replace fixed hybrid weights with a learned reranker.
   Add field-aware embeddings:
   semantic on gloss/meaning text
   form on transliteration/IPA/script
   root-aware features separately
   Experiment with cognate-aware contrastive fine-tuning.
   Only after that, test Procrustes alignment or GNNs.
   Leave vector DB and hyperbolic methods for much later.
   My blunt take
   Gemini’s answer is research-smart, but some of it jumps too quickly to advanced methods before the repo has the evaluation and modularity needed to support them safely.

   The best immediate technical move is not “adopt hyperbolic embeddings” or “move to Qdrant.”
   It is:

   define what success means,
   create labeled data,
   learn a better scorer,
   then train embeddings specifically for cognacy.
   If you want, I can turn Gemini’s ideas plus mine into a single ranked roadmap:

   now
   next
   later
   with concrete repo changes for each phase.

   yes  turn Gemini’s ideas plus yours into a single ranked roadmap:

   now
   next
   later
   with concrete repo changes for each phase.


   Now

   The goal in this phase is to improve retrieval quality without taking on heavy research risk.

   Create a real evaluation set
   Add a benchmark package under [Juthoor-CognateDiscovery-LV2/resources](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\resources)
   and [Juthoor-CognateDiscovery-LV2/tests](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\tests).
   Concrete changes:

   Add resources/benchmarks/cognate_gold.jsonl
   Add resources/benchmarks/non_cognate_translations.jsonl
   Add resources/benchmarks/false_friends.jsonl
   Add scripts/discovery/evaluate.py
   Add tests for score regression and metric sanity
   Metrics to report:
   Recall@k
   MRR
   nDCG
   precision by language pair
   Refactor LV2 into composable modules
   [run_discovery_retrieval.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\scripts\discovery\run_discovery_retrieval.py)
   currently does too much.
   Concrete changes:

   Move corpus discovery into src/.../discovery/corpora.py
   Move retrieval orchestration into src/.../discovery/retrieval.py
   Move output/report logic into src/.../discovery/reporting.py
   Keep the script as a thin CLI wrapper only
   This is the prerequisite for fast experimentation.
   Make embeddings field-aware
   Right now the pipeline mostly embeds lemma text. That is too weak for this task.
   Concrete changes:

   Promote form_text and meaning_text to required downstream fields in LV0
   Extend [Juthoor-DataCore-LV0/src/juthoor_datacore_lv0/features/build_text_fields.py](C:\Users\yassi\AI
   Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\src\juthoor_datacore_lv0\features\build_text_fields.py)
   Add validation rules in LV0 so downstream corpora declare whether they are embedding-ready
   Update LV2 embedding code to use:
   semantic model on meaning_text
   form model on form_text
   This is the highest-leverage model-side change.
   Replace fixed hybrid weights with a learned reranker
   Gemini’s dynamic weighting idea is right, but start simple.
   Concrete changes:

   Keep FAISS retrieval as-is
   Add a reranking stage after top-k retrieval
   Train a simple scorer on existing features:
   semantic
   form
   orthography
   sound
   skeleton
   same-family flag
   Put this in src/.../discovery/rerank.py
   Make [hybrid_scoring.py](C:\Users\yassi\AI
   Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) the baseline, not the final scorer
   Start with logistic regression or gradient boosting, not attention.
   Tighten schema/versioning
   Concrete changes:

   Add schema_version and embedding_fields_version to LV0 rows/manifests
   Add typed row/result models in LV0 and LV2
   Validate required fields before indexing
   This reduces silent drift.
   Next

   This phase is where Gemini’s stronger research ideas become worth implementing.

   Train cognate-aware contrastive embeddings
   This is the best medium-term upgrade.
   Concrete changes:

   Add scripts/training/train_contrastive.py
   Create pair/triplet training data from gold anchors
   Fine-tune a form-oriented encoder first
   Keep semantic and genealogical signals separate
   Training objective should distinguish:
   cognate pairs
   translation-but-not-cognate pairs
   false friends
   borrowings where possible
   This is where the project starts moving beyond generic semantic retrieval.
   Introduce language-pair-specific calibration
   Instead of one universal scorer, have calibrated scoring profiles.
   Concrete changes:

   Add scorer configs per pair/family under resources/scoring_profiles/
   Examples:
   arabic_hebrew.yaml
   arabic_english.yaml
   arabic_latin.yaml
   Load these at rerank time
   This implements Gemini’s “dynamic sound corridor weighting” in a controlled way.
   Improve phonological and correspondence normalization
   Before more model complexity, upgrade the linguistic preprocessing.
   Concrete changes:

   Add src/.../discovery/correspondences.py
   Add normalized feature transforms for:
   Arabic weak radicals
   hamza variants
   emphatic/plain correspondences
   transliteration normalization
   Semitic consonant corridor classes
   Feed those features into the reranker and contrastive training
   This will likely improve both accuracy and explainability.
   Add root-level retrieval alongside lexeme-level retrieval
   The project’s core object is not only the lemma.
   Concrete changes:

   Build aggregated root-family records in LV0/LV1
   Add a second index type in LV2:
   lexeme_index
   root_family_index
   Let runs choose one or both
   This fits the repo’s actual theory much better.
   Experiment with Procrustes alignment
   Good candidate for a contained research track.
   Concrete changes:

   Add experimental module src/.../discovery/alignment.py
   Train family-specific spaces
   Align them with curated anchor concepts
   Evaluate against the same benchmark, not intuition
   This should stay behind an experiment flag until proven.
   Later

   These are worthwhile only after the baseline is measured and stable.

   Graph neural models on LV1/LV2 structure
   Gemini’s GNN idea belongs here.
   Concrete changes:

   Define a stable graph export schema from LV1/LV2
   Add node types such as root, lemma, concept, language
   Add experimental GNN training scripts under scripts/graph/
   Compare GNN embeddings against the non-graph benchmark
   This could help LV3 a lot, but only after the graph itself is trustworthy.
   Vector database migration
   Useful for operations, not core research quality.
   Concrete changes:

   Abstract index backend behind an interface
   Keep FAISS as default
   Add optional Qdrant backend for filtering and interactive search
   Do this when you need:
   persistent services
   multi-user access
   richer metadata filtering
   Hyperbolic embeddings for LV3 genealogy modeling
   This is a theory-layer experiment, not an LV2 retrieval fix.
   Concrete changes:

   Build a separate LV3 experimental module for hierarchical embedding
   Use validated corridor/root-family structures, not raw lexeme retrieval
   Evaluate whether it helps lineage reconstruction more than standard graph methods
   I would keep this out of the main pipeline until there is a clear win.
   Full model-serving and experiment tracking
   Concrete changes:

   add run manifests with corpus hashes, model ids, feature versions, git commit
   add MLflow or lightweight experiment logs
   make every discovery run reproducible
   This becomes important once you have multiple learned models in play.
   Recommended execution order

   If I were driving the repo, I’d do it in this exact order:

   benchmark + metrics
   LV2 refactor
   field-aware embeddings
   learned reranker
   phonological/correspondence features
   contrastive cognate training
   language-pair calibration
   root-family retrieval
   Procrustes experiments
   GNN experiments
   vector DB
   hyperbolic LV3 experiments
   The short version is: improve measurement first, then scoring, then train custom embeddings, then try graph/hierarchy methods.

   If you want, I can
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  Responding with gemini-3-flash-preview
✦ I've reviewed the critique and the synthesized roadmap. The feedback is highly pragmatic and technically sound. It correctly identifies that jumping into hyperbolic
  embeddings or GNNs without a Gold Evaluation Set is "research-heavy" and risky.


  The core realization—"semantic similarity != cognate similarity"—is the compass for all these changes. I fully agree with this prioritized roadmap.


  Why this Roadmap is Superior:
   1. Measurement First: By building a cognate_gold.jsonl, we move from "this looks right" to "this is 15% more accurate." This is the hallmark of a mature engineering
      project.
   2. Field-Awareness: Separating the Form (IPA/Translit) from the Meaning (Gloss) when embedding is the single most effective "surgical" change we can make to the existing
      pipeline.
   3. Reranking over Replacing: Keeping FAISS/BGE-M3 for broad retrieval and using a learned reranker for the top-k results is a standard, high-performance industry
      pattern.

  ---


  Phase 1: The "Now" Execution Plan
  I am ready to start implementing the "Now" phase immediately. Based on the roadmap, here is how I suggest we begin:


  Step 1: Establish the Benchmark & Eval Framework
  We cannot improve what we cannot measure. I'll create the directory structure and the initial evaluation script.
   * Action: Create Juthoor-CognateDiscovery-LV2/resources/benchmarks/ and a skeleton for evaluate.py.


  Step 2: LV2 Refactor (Decoupling)
  I noticed during my research that run_discovery_retrieval.py is indeed acting as a monolithic script. I'll begin modularizing it so we can easily swap out scoring logic.
   * Action: Move core logic into src/juthoor_cognatediscovery_lv2/discovery/.


  Step 3: Field-Aware Embeddings
  I will check the current implementation of build_text_fields.py in LV0 to ensure it's generating the form_text and meaning_text needed for the upgraded embeddings.

  ---


  Would you like me to start with Step 1 (creating the benchmark structure) or Step 2 (refactoring the retrieval script)? I recommend starting with the Benchmark, as it
  will give us a "baseline" score for the current system before we change any code. No code changes should be made without a way to prove they are an improvement.

                                                                                                                                                            ? for shortcuts
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 shift+tab to accept edits                                                                                                                  1 GEMINI.md file | 1 MCP server
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
 >   Type your message or @path/to/file
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
 ~\AI Projects\Juthoor-Linguistic-Genealogy (main*)                        no sandbox (see /docs)                        /model Auto (Gemini 3) 96% context left | 346.3 MB





Codex:

understand the technical aspects of this project


Worked for 2m 24s
This repo is a Python workspace monorepo for a staged linguistics pipeline, not a single application. The root [pyproject.toml](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\pyproject.toml) defines five workspace members: LV0 data ingestion, LV1 Arabic genome, LV2 cognate discovery, LV3 theory/origins, and a separate Qur’an analysis package. The top-level architecture described in [README.md](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\README.md) and [docs/PROJECT_OVERVIEW.md](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\docs\PROJECT_OVERVIEW.md) matches the code layout.

Technically, the core implemented system is LV0 + LV2. LV0 exposes the ldc CLI from [Juthoor-DataCore-LV0/src/juthoor_datacore_lv0/cli.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\src\juthoor_datacore_lv0\cli.py), which shells into a step runner in [Juthoor-DataCore-LV0/src/juthoor_datacore_lv0/ingest/runner.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\src\juthoor_datacore_lv0\ingest\runner.py). That runner defines a deterministic ingest pipeline over raw linguistic sources and writes canonical JSONL outputs under data/processed/. It handles Arabic root maps, Qur’anic morphology, Hugging Face Arabic roots, Kaikki/Wiktionary corpora, and text-field enrichment. The package metadata in [Juthoor-DataCore-LV0/pyproject.toml](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\pyproject.toml) shows LV0 is intentionally lightweight: mainly pandas and numpy, with validation and packaging around canonical datasets.

LV2 is the main ML/retrieval layer. The entry point [Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\scripts\discovery\run_discovery_retrieval.py) supports both interactive and CLI workflows, discovers corpora automatically, embeds source/target lexemes, caches vectors, builds FAISS indexes, and writes ranked discovery leads as JSONL plus an HTML report. The scoring logic in [Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/lv3/discovery/hybrid_scoring.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) combines semantic, form, orthographic, phonetic, and consonantal-skeleton similarity, with an optional same-family boost. [Juthoor-CognateDiscovery-LV2/src/juthoor_cognatediscovery_lv2/lv3/discovery/index.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\index.py) wraps FAISS index persistence. Its dependency model in [Juthoor-CognateDiscovery-LV2/pyproject.toml](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\pyproject.toml) is modular: base package + optional local ML extras (faiss-cpu, torch, transformers, FlagEmbedding) or an API backend.

LV1 is real but more script-oriented than framework-oriented. [Juthoor-ArabicGenome-LV1/scripts/build_genome_phase1.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-ArabicGenome-LV1\scripts\build_genome_phase1.py) reads LV0 Arabic lexemes and groups them by BAB -> binary_root -> root_norm -> lemmas, writing per-letter genome JSONL files. [Juthoor-ArabicGenome-LV1/scripts/build_genome_phase2.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-ArabicGenome-LV1\scripts\build_genome_phase2.py) enriches those outputs with Mu‘jam-derived semantic overlays. LV1 depends on LV0 and networkx per [Juthoor-ArabicGenome-LV1/pyproject.toml](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-ArabicGenome-LV1\pyproject.toml), but most of the current logic lives in scripts and generated outputs rather than a large reusable src/ codebase.

LV3 is mostly a blueprint at this point. [Juthoor-Origins-LV3/pyproject.toml](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-Origins-LV3\pyproject.toml) mainly wires dependencies on LV1 and LV2, while the folder contains docs, templates, and theory material more than implemented pipeline code. The Qur’an package is similarly narrower in scope: [Quran-Corpus-Analysis/README.md](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Quran-Corpus-Analysis\README.md) and [Quran-Corpus-Analysis/docs/START_HERE.md](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Quran-Corpus-Analysis\docs\START_HERE.md) show it is an analysis layer over Qur’anic morphology and verse clustering, driven by scripts rather than a service or UI.

A few practical observations matter if you work on this repo:

It is data-heavy and many directories under data/processed/, outputs/, and Resources/ are artifacts rather than source code.
The workspace is currently dirty with untracked/generated data, so any changes should avoid assuming a clean git state.
The repo mixes “implemented production path” code with “scaffold/placeholder” code. For example, LV0’s text-field builder in [Juthoor-DataCore-LV0/src/juthoor_datacore_lv0/features/build_text_fields.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\src\juthoor_datacore_lv0\features\build_text_fields.py) is explicitly scaffold-like, while the ingest runner and LV2 retrieval script are materially implemented.
If you want, I can turn this into one of these next:

a “how to run the whole stack” walkthrough,
a “where to change what” maintainer map,
a code-level deep dive on LV0, LV2, or the Qur’an analysis package.

any technical aspect you suggest to upgrade or change? for example the embeding techiniques? 

Yes. The biggest upgrades I’d suggest are not “use a newer model” first. The repo’s main technical gap is that retrieval, data contracts, and validation maturity are uneven across levels. I’d prioritize these changes.

Highest Value Changes

Promote LV2 from script pipeline to package API
[Juthoor-CognateDiscovery-LV2/scripts/discovery/run_discovery_retrieval.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\scripts\discovery\run_discovery_retrieval.py) is doing orchestration, corpus discovery, embedding, indexing, scoring, and output writing in one place.
Split it into reusable modules:

corpus registry
embedding service
retrieval service
reranker
report/export
This will make experimentation much easier and reduce regression risk.
Version the canonical row schema explicitly
LV0 has schema docs, but the code still feels partly scaffolded.
Add a strict schema version field to every processed JSONL row and validate it in CI. Right now downstream layers depend on fields like lemma, ipa, root_norm, binary_root, form_text, meaning_text, but the contract is only partially enforced.

Separate retrieval from scoring more cleanly
Right now LV2 mixes dense retrieval and heuristic reranking. That is fine for a prototype, but for research quality you want:

retrieval stage: high recall
rerank stage: high precision
evaluation stage: measured quality
The current hybrid score in [hybrid_scoring.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) is reasonable, but it should be treated as a reranker, not the main retrieval logic.
Embedding Upgrades

Stop embedding only lemma text
In LV2, embeddings are built from a cleaned lemma string only. That is too lossy for lexical comparison.
Build multiple text views per lexeme:

form_text: script + transliteration + IPA
meaning_text: gloss/definition
optional context_text: POS + root + short semantic notes
Then use:
semantic embeddings on meaning_text
form embeddings on form_text
This is a bigger improvement than swapping BGE-M3 for another model.
Use two-tower retrieval plus cross-encoder reranking
Current stack:

semantic dense model
form dense model
heuristic fusion
Better stack:
retrieve with dense semantic + dense form indexes
rerank top N with a stronger pairwise model or learned scorer
Even a lightweight learned reranker over your existing features would likely outperform fixed weights.
Make embeddings field-aware
Instead of one vector per lexeme, store separate vectors:

meaning_vec
form_vec
maybe root_vec
Then combine at query time by language pair.
Example: Arabic to English should weight meaning more; Arabic to Hebrew/Aramaic may weight skeleton/form more.
Replace fixed hybrid weights with learned calibration
The hardcoded weights in [HybridWeights](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) are fine for bootstrapping, but they should become:

language-pair-specific
learned from labeled positives/negatives
Start with logistic regression or gradient boosting on:
semantic score
form score
orthography score
sound score
skeleton score
same-family flag
Linguistics-Specific Improvements

Improve phonological normalization before embedding
The current skeleton logic is useful but shallow.
Add a proper normalization layer for:

Arabic weak radicals
hamza variants
emphatic/coronal equivalence classes
Semitic consonant correspondences
Greek/Latin transliteration normalization
This will improve both heuristic scoring and form embeddings.
Build correspondence-aware matching
Cognate discovery should not rely only on raw similarity. Add explicit sound correspondence rules or feature transforms.
Example:

Arabic q vs Hebrew q/k
Arabic emphatics vs plain stops in borrowings
Semitic th/dh/z drift
This would materially improve recall and explainability.
Treat roots and lemmas as separate entities
Right now lexeme rows carry root information, but the retrieval unit is still mostly the lexeme.
Add a second retrieval mode:

lexeme-to-lexeme
root-family-to-root-family
For this project, root-family retrieval is probably central, not optional.
Data and Evaluation

Create a gold evaluation set
This is the most important missing piece if you want to improve embeddings seriously.
Build a benchmark with:
confirmed cognates
false friends
semantically similar but unrelated pairs
borrowing vs inherited distinctions
Without this, changing models is guesswork.
Add offline metrics and regression tracking
Each run should report:
recall@k
MRR
nDCG
precision in top buckets
per-language-pair breakdown
Then model upgrades become measurable.
Move corpus discovery into a manifest instead of filesystem scanning
The interactive wizard currently scans data/processed/ dynamically.
That is convenient but brittle.
Add a corpus manifest with:
language
stage
source quality
row count
fields available
embedding readiness
This will make reproducibility much better.
Engineering Upgrades

Unify outputs and cache layout
LV2 caches embeddings and indexes under ad hoc output paths.
Introduce a run manifest containing:
corpus hashes
model ids
embedding config
score config
git commit
Then cached vectors become traceable and safe to reuse.
Add typed models for rows and results
This repo passes around raw dicts heavily.
Introduce dataclasses or Pydantic models for:
canonical lexeme row
retrieval candidate
scored lead
run manifest
That will reduce silent schema drift.
What I would change first

If I had to pick only 4 upgrades:

Embed meaning_text and form_text separately instead of lemma-only.
Add a gold benchmark and metrics.
Convert hybrid weights from fixed constants to a learned reranker.
Refactor LV2 into reusable modules instead of one large script.
If you want, I can do the next step concretely and produce either:

a prioritized upgrade roadmap for this repo, or
a technical design for a better embedding/retrieval stack that fits the current codebase.

i liked your ideas so much, when i asked gemini the same question about this project he said the following what do you think :  Based on the current architecture and the specific goals of tracing linguistic genealogy (which is different from standard semantic search), here are several technical
  upgrades and changes I would suggest, particularly regarding the embedding techniques and the data pipeline:


  1. Transition to "Cognate-Aware" Contrastive Learning
  Currently, you use BGE-M3 and SONAR, which are optimized for semantic similarity (synonyms). However, genealogy requires genealogical similarity (cognates).
   * The Problem: BGE-M3 might give a high score to "Dog" (English) and "Kalb" (Arabic for 'dog') because they mean the same thing, even though they are etymologically
     unrelated. It might give a low score to "Horn" (English) and "Qarn" (Arabic), which are likely cognates but have different semantic nuances in modern contexts.
   * The Upgrade: Use a Triplet Loss or Contrastive Learning approach to fine-tune your ByT5/CANINE models using your "Gold" anchor pairs. This would train the embedding
     space to ignore "noise" (vowel shifts) and focus on "signal" (consonantal correspondences) specific to the sound corridors you've identified.


  2. Hyperbolic Embeddings for Hierarchical Data
  Language genealogy is inherently tree-like (hierarchical).
   * The Problem: Standard Euclidean embeddings (like those used in FAISS or BGE-M3) struggle to represent hierarchical structures accurately without high distortion.
   * The Upgrade: Explore Poincaré Embeddings (Hyperbolic space). These are mathematically optimized to represent hierarchies. In a hyperbolic embedding space, the
     "distance" between nodes grows exponentially as you move toward the leaves, which perfectly mirrors the divergence of languages from a common root (the "Origin").


  3. Cross-Lingual Mapping (Procrustes Alignment)
  Instead of relying on a single multilingual model like SONAR, which is a "black box," you could align language-specific spaces.
   * The Upgrade: Train high-quality embeddings for Arabic/Semitic and Indo-European languages separately on historical corpora, then use Orthogonal Procrustes Alignment to
     map them into a shared space using your 536 "Anchor Concepts" as the transformation matrix. This preserves the internal linguistic relationships of each family better
     than a generic multilingual model.


  4. Integration of Graph Neural Networks (GNNs)
  Your LV1 and LV2 data is essentially a graph (Roots → Lemmas → Cognates).
   * The Upgrade: Implement a GraphSAGE or GAT (Graph Attention Network) layer over your Neo4j exports. Instead of comparing two isolated words, a GNN can produce an
     embedding for a word based on its context in the root graph (e.g., what other words share this biconsonantal root?). This would allow LV3 to "see" that two words are
     related because their "root neighborhoods" look similar.


  5. Shift to a Vector Database (Scalability)
  As you move from 500 concepts to 10,000+ lemmas across 20+ languages, managing static FAISS files will become cumbersome.
   * The Upgrade: Integrate a vector database like Qdrant or Weaviate. These support "Hybrid Search" natively—allowing you to combine vector similarity (embeddings) with
     metadata filtering (e.g., lemma_status == 'gold') and keyword matching in a single query.


  6. Dynamic "Sound Corridor" Weighting
   * The Upgrade: Instead of a static 10% weight for the "Skeleton" score, you could use an Attention Mechanism that learns which component (Orthography vs. Sound vs.
     Skeleton) is most reliable for specific language pairs. For example, when comparing Maltese and Arabic, Orthography might get more weight; when comparing Hittite and
     Arabic, the Skeleton/IPA might be prioritized.

A lot of that is strong. The best parts of Gemini’s answer are the ones that match the actual failure mode of this repo: semantic similarity is not the same as genealogical relatedness.

My view is:

Mostly right

Cognate-aware contrastive learning
This is the strongest suggestion in that list.
The current stack is still too semantic-first. For this project, a model trained to separate:

cognates
non-cognate translations
borrowings
false friends
would be more valuable than swapping generic embedding models.
I agree with the direction, with one caveat: don’t start with full end-to-end fine-tuning immediately. First build a labeled benchmark and a simple learned reranker. If that works, then move to contrastive fine-tuning.
Dynamic weighting
Also strong.
Static weights in [hybrid_scoring.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) are a bootstrap mechanism, not a final method.
Different language pairs need different evidence weights. Arabic-Hebrew is not Arabic-English, and neither is Arabic-Latin.
I would implement this first as:

language-pair-specific calibrated models
then maybe attention/gating later
An explicit learned scorer is simpler and easier to debug than adding attention too early.
GNNs
Directionally good, but later-stage.
If LV1/LV2 graphs become central objects, graph-based representation learning could help. But I would not do this before:

the node/edge schema is stable
you have a gold benchmark
the non-graph baseline is already strong
Otherwise you’ll add complexity without knowing if the gain is real.
Promising but not first priority
4. Procrustes alignment
This is intellectually plausible and more transparent than relying only on a generic multilingual model.
But it depends on having:

solid language-specific spaces
enough reliable anchors
a clean shared concept inventory
If your anchor concepts are good, this could be excellent for experiments. I still wouldn’t make it the first big investment because it’s research-heavy and sensitive to anchor quality.
Vector database
Reasonable eventually, but not urgent.
For the current scale, FAISS files are fine. A vector DB helps when you need:
serving
filtering-heavy workflows
concurrent querying
persistent operational infrastructure
Right now the bigger issue is retrieval quality, not storage technology.
I would keep FAISS until the data/model pipeline stabilizes.
Interesting, but I would push back
6. Hyperbolic embeddings
This is the weakest recommendation in practical terms.
The theory makes sense because genealogy is hierarchical, but your actual task is not just tree reconstruction. It is a messy mix of:

inheritance
borrowing
semantic drift
root-pattern morphology
partial correspondences across families
That structure is not a clean tree. It is more like a graph with competing signals.
Hyperbolic embeddings may become useful at LV3 for lineage modeling, but they are not where I would spend time for LV2 retrieval. They are likely too far downstream from your main bottleneck.
Where I agree most strongly with Gemini
The core insight is this:

semantic similarity != cognate similarity

That is exactly right, and it is the main technical limitation of using generic multilingual embeddings as the dominant signal.

What I would change in Gemini’s plan
I’d reorder it like this:

Build a gold evaluation set.
Replace fixed hybrid weights with a learned reranker.
Add field-aware embeddings:
semantic on gloss/meaning text
form on transliteration/IPA/script
root-aware features separately
Experiment with cognate-aware contrastive fine-tuning.
Only after that, test Procrustes alignment or GNNs.
Leave vector DB and hyperbolic methods for much later.
My blunt take
Gemini’s answer is research-smart, but some of it jumps too quickly to advanced methods before the repo has the evaluation and modularity needed to support them safely.

The best immediate technical move is not “adopt hyperbolic embeddings” or “move to Qdrant.”
It is:

define what success means,
create labeled data,
learn a better scorer,
then train embeddings specifically for cognacy.
If you want, I can turn Gemini’s ideas plus mine into a single ranked roadmap:

now
next
later
with concrete repo changes for each phase.

yes  turn Gemini’s ideas plus yours into a single ranked roadmap: 

now
next
later
with concrete repo changes for each phase.


Now

The goal in this phase is to improve retrieval quality without taking on heavy research risk.

Create a real evaluation set
Add a benchmark package under [Juthoor-CognateDiscovery-LV2/resources](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\resources) and [Juthoor-CognateDiscovery-LV2/tests](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\tests).
Concrete changes:

Add resources/benchmarks/cognate_gold.jsonl
Add resources/benchmarks/non_cognate_translations.jsonl
Add resources/benchmarks/false_friends.jsonl
Add scripts/discovery/evaluate.py
Add tests for score regression and metric sanity
Metrics to report:
Recall@k
MRR
nDCG
precision by language pair
Refactor LV2 into composable modules
[run_discovery_retrieval.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\scripts\discovery\run_discovery_retrieval.py) currently does too much.
Concrete changes:

Move corpus discovery into src/.../discovery/corpora.py
Move retrieval orchestration into src/.../discovery/retrieval.py
Move output/report logic into src/.../discovery/reporting.py
Keep the script as a thin CLI wrapper only
This is the prerequisite for fast experimentation.
Make embeddings field-aware
Right now the pipeline mostly embeds lemma text. That is too weak for this task.
Concrete changes:

Promote form_text and meaning_text to required downstream fields in LV0
Extend [Juthoor-DataCore-LV0/src/juthoor_datacore_lv0/features/build_text_fields.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-DataCore-LV0\src\juthoor_datacore_lv0\features\build_text_fields.py)
Add validation rules in LV0 so downstream corpora declare whether they are embedding-ready
Update LV2 embedding code to use:
semantic model on meaning_text
form model on form_text
This is the highest-leverage model-side change.
Replace fixed hybrid weights with a learned reranker
Gemini’s dynamic weighting idea is right, but start simple.
Concrete changes:

Keep FAISS retrieval as-is
Add a reranking stage after top-k retrieval
Train a simple scorer on existing features:
semantic
form
orthography
sound
skeleton
same-family flag
Put this in src/.../discovery/rerank.py
Make [hybrid_scoring.py](C:\Users\yassi\AI Projects\Juthoor-Linguistic-Genealogy\Juthoor-CognateDiscovery-LV2\src\juthoor_cognatediscovery_lv2\lv3\discovery\hybrid_scoring.py) the baseline, not the final scorer
Start with logistic regression or gradient boosting, not attention.
Tighten schema/versioning
Concrete changes:

Add schema_version and embedding_fields_version to LV0 rows/manifests
Add typed row/result models in LV0 and LV2
Validate required fields before indexing
This reduces silent drift.
Next

This phase is where Gemini’s stronger research ideas become worth implementing.

Train cognate-aware contrastive embeddings
This is the best medium-term upgrade.
Concrete changes:

Add scripts/training/train_contrastive.py
Create pair/triplet training data from gold anchors
Fine-tune a form-oriented encoder first
Keep semantic and genealogical signals separate
Training objective should distinguish:
cognate pairs
translation-but-not-cognate pairs
false friends
borrowings where possible
This is where the project starts moving beyond generic semantic retrieval.
Introduce language-pair-specific calibration
Instead of one universal scorer, have calibrated scoring profiles.
Concrete changes:

Add scorer configs per pair/family under resources/scoring_profiles/
Examples:
arabic_hebrew.yaml
arabic_english.yaml
arabic_latin.yaml
Load these at rerank time
This implements Gemini’s “dynamic sound corridor weighting” in a controlled way.
Improve phonological and correspondence normalization
Before more model complexity, upgrade the linguistic preprocessing.
Concrete changes:

Add src/.../discovery/correspondences.py
Add normalized feature transforms for:
Arabic weak radicals
hamza variants
emphatic/plain correspondences
transliteration normalization
Semitic consonant corridor classes
Feed those features into the reranker and contrastive training
This will likely improve both accuracy and explainability.
Add root-level retrieval alongside lexeme-level retrieval
The project’s core object is not only the lemma.
Concrete changes:

Build aggregated root-family records in LV0/LV1
Add a second index type in LV2:
lexeme_index
root_family_index
Let runs choose one or both
This fits the repo’s actual theory much better.
Experiment with Procrustes alignment
Good candidate for a contained research track.
Concrete changes:

Add experimental module src/.../discovery/alignment.py
Train family-specific spaces
Align them with curated anchor concepts
Evaluate against the same benchmark, not intuition
This should stay behind an experiment flag until proven.
Later

These are worthwhile only after the baseline is measured and stable.

Graph neural models on LV1/LV2 structure
Gemini’s GNN idea belongs here.
Concrete changes:

Define a stable graph export schema from LV1/LV2
Add node types such as root, lemma, concept, language
Add experimental GNN training scripts under scripts/graph/
Compare GNN embeddings against the non-graph benchmark
This could help LV3 a lot, but only after the graph itself is trustworthy.
Vector database migration
Useful for operations, not core research quality.
Concrete changes:

Abstract index backend behind an interface
Keep FAISS as default
Add optional Qdrant backend for filtering and interactive search
Do this when you need:
persistent services
multi-user access
richer metadata filtering
Hyperbolic embeddings for LV3 genealogy modeling
This is a theory-layer experiment, not an LV2 retrieval fix.
Concrete changes:

Build a separate LV3 experimental module for hierarchical embedding
Use validated corridor/root-family structures, not raw lexeme retrieval
Evaluate whether it helps lineage reconstruction more than standard graph methods
I would keep this out of the main pipeline until there is a clear win.
Full model-serving and experiment tracking
Concrete changes:

add run manifests with corpus hashes, model ids, feature versions, git commit
add MLflow or lightweight experiment logs
make every discovery run reproducible
This becomes important once you have multiple learned models in play.
Recommended execution order

If I were driving the repo, I’d do it in this exact order:

benchmark + metrics
LV2 refactor
field-aware embeddings
learned reranker
phonological/correspondence features
contrastive cognate training
language-pair calibration
root-family retrieval
Procrustes experiments
GNN experiments
vector DB
hyperbolic LV3 experiments
The short version is: improve measurement first, then scoring, then train custom embeddings, then try graph/hierarchy methods.

If you want, I can next convert this roadmap into a concrete implementation plan tied to exact files and new modules for this repo.


