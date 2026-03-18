# LV1 Core Restructure — Structure First, Content Later

> **For agentic workers:** This plan builds LV1 as a content-ready semantic engine. Schemas and registries now, curated theory content later via an import inbox.

**Goal:** Turn LV1 from a collection of experiments into the formal computational core of the Arabic Tongue theory, with structured registries, an import pipeline, and graceful degradation for missing content.

**Owner:** Codex (primary), Opus (review)
**Baseline commit:** `a2a5893`

---

## Agent Split

| Agent | Scope |
|-------|-------|
| **Codex** | LV1 Phases 1-5: build registries, import system, pipeline, attach research outputs, Quranic bridge |
| **Sonnet/Opus** | LV2 evaluation: finish Waves 1-3 discovery runs, reranker training, multi-pair review |

These run in parallel. No dependencies between them.

---

## Architecture

### Two Layers

**A. Structural layer (build now)**
- Registry schemas (frozen dataclasses)
- Import formats and validators
- Status state machine: `empty → draft → curated → tested → promoted → rejected`
- Processing pipeline contracts
- Output contracts for QCA/LV3

**B. Content layer (populated later)**
- Letter meanings (user provides via inbox folder)
- Binary field glosses (user provides via inbox folder)
- Root composition rules (user provides via inbox folder)
- Scholar-specific interpretations
- Quranic contrast pairs

### Theory Content Inbox

```
Juthoor-ArabicGenome-LV1/data/theory_canon/
├── inbox/                  ← user drops curated JSONL files here
│   ├── letters/            ← letter semantic entries
│   ├── binary_fields/      ← binary field glosses
│   ├── root_composition/   ← composition rules
│   ├── theory_claims/      ← scholar claims with provenance
│   └── quranic/            ← Quranic interpretation data
├── imported/               ← files move here after successful ingestion
├── rejected/               ← files that failed validation
└── SCHEMA.md               ← documents expected format per subfolder
```

All content files must be:
- UTF-8 JSONL
- Stable IDs
- Explicit provenance fields
- One record per line

---

## Phase 1 — Build The Empty Canon

### Task 1.1 — Registry Dataclasses

**File:** `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/canon_models.py`

Create frozen dataclasses (extend existing `core/models.py` pattern):

```python
@dataclass(frozen=True)
class SourceEntry:
    source_id: str
    scholar: str                    # jabal, neili, asim_al_masri, hassan_abbas, ibn_jinni, samarrai
    claim_type: str                 # semantic, kinetic, sensory, articulatory
    claim_text: str
    document_ref: str
    curation_status: str            # raw, reviewed, accepted

@dataclass(frozen=True)
class LetterSemanticEntry:
    letter: str                     # single Arabic letter
    letter_name: str                # e.g. "الباء"
    canonical_semantic_gloss: str | None
    canonical_kinetic_gloss: str | None
    canonical_sensory_gloss: str | None
    articulatory_features: dict | None
    sources: tuple[SourceEntry, ...]
    agreement_level: str            # consensus, majority, contested, unknown
    confidence_tier: str            # high, medium, low, stub
    status: str                     # empty, draft, curated, tested, promoted, rejected

@dataclass(frozen=True)
class BinaryFieldEntry:
    binary_root: str                # two-letter root e.g. "حس"
    field_gloss: str | None
    field_gloss_source: str | None  # scholar who defined this gloss
    letter1: str
    letter2: str
    letter1_gloss: str | None
    letter2_gloss: str | None
    member_roots: tuple[str, ...]
    member_count: int
    coherence_score: float | None
    cross_lingual_support: dict | None  # {"hebrew": bool, "aramaic": bool}
    status: str

@dataclass(frozen=True)
class RootCompositionEntry:
    root: str                       # trilateral root
    binary_root: str
    third_letter: str
    conceptual_root_meaning: str | None
    binary_field_meaning: str | None
    axial_meaning: str | None
    letter_trace: tuple[dict, ...] | None
    position_profile: dict | None
    modifier_profile: dict | None
    compositional_signal: float | None
    agreement_with_observed_gloss: str | None  # resolved, partial, drift, contradiction
    status: str

@dataclass(frozen=True)
class TheoryClaim:
    claim_id: str
    theme: str                      # intentionality, no_synonymy, letter_semantics, binary_derivation, positional, quranic_method
    scholar: str
    statement: str
    scope: str                      # arabic_general, quranic_only, comparative_semitic
    evidence_type: str              # doctrinal, lexical, phonetic, interpretive, comparative
    source_doc: str
    source_locator: str | None
    status: str                     # asserted, curated, tested, promoted, rejected

@dataclass(frozen=True)
class QuranicSemanticProfile:
    lemma: str
    root: str
    conceptual_meaning: str | None
    binary_field_meaning: str | None
    letter_trace: tuple[dict, ...] | None
    contextual_constraints: tuple[str, ...] | None
    contrast_lemmas: tuple[str, ...] | None
    interpretive_notes: str | None
    confidence: str                 # high, medium, low, stub
    status: str
```

**Tests:** `tests/test_canon_models.py`
- Each dataclass can be instantiated with minimal fields
- Status values are validated
- Frozen immutability holds

### Task 1.2 — Canon Loaders

**File:** `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/canon_loaders.py`

Functions that load registry entries from JSONL files:

```python
def load_letter_registry(path: Path | None = None) -> dict[str, LetterSemanticEntry]:
    """Load letter semantics registry. Returns dict keyed by letter."""

def load_binary_field_registry(path: Path | None = None) -> dict[str, BinaryFieldEntry]:
    """Load binary field registry. Returns dict keyed by binary_root."""

def load_root_composition_registry(path: Path | None = None) -> dict[str, RootCompositionEntry]:
    """Load root composition registry. Returns dict keyed by root."""

def load_theory_claims(path: Path | None = None) -> list[TheoryClaim]:
    """Load theory claims."""

def load_quranic_profiles(path: Path | None = None) -> dict[str, QuranicSemanticProfile]:
    """Load Quranic semantic profiles. Returns dict keyed by lemma."""
```

Default paths point to `data/theory_canon/` subdirectories.

**Tests:** `tests/test_canon_loaders.py`
- Load from empty folder → returns empty dict
- Load from folder with valid JSONL → returns populated entries
- Load from folder with malformed JSONL → raises validation error

### Task 1.3 — Seed Registries From Existing Data

**Script:** `scripts/canon/seed_registries.py`

Migration from current LV1 data to canon registries:

| Source | Target | Fields |
|--------|--------|--------|
| `data/muajam/letter_meanings.jsonl` | Letter Semantics Registry | letter, letter_name, articulatory_features |
| `data/muajam/roots.jsonl` + BinaryRoot loader | Binary Field Registry | binary_root, member_roots, member_count |
| `outputs/research_factory/promoted/field_coherence_scores.jsonl` | Binary Field Registry | coherence_score |
| `outputs/research_factory/promoted/positional_profiles.jsonl` | Letter Semantics Registry | (attach as evidence) |
| `outputs/research_factory/promoted/metathesis_pairs.jsonl` | Binary Field Registry | (attach as evidence) |
| `outputs/genome_v2/*.jsonl` | Root Composition Registry | root, binary_root, third_letter, axial_meaning |

All seeded entries get `status: "draft"` — they are structurally populated but not yet curated.

**Tests:**
- Seed script runs without error on current repo data
- All 28 letters have registry rows after seeding
- All binary roots from Muajam have registry rows after seeding
- Coherence scores from H2 attach to correct binary entries

### Task 1.4 — Create Theory Content Inbox

Create the folder structure and SCHEMA.md:

**File:** `Juthoor-ArabicGenome-LV1/data/theory_canon/SCHEMA.md`

Document expected format for each subfolder with examples.

**File:** `Juthoor-ArabicGenome-LV1/data/theory_canon/inbox/.gitkeep` (and subfolders)

### Task 1.5 — Phase 1 Acceptance Tests

**File:** `tests/test_canon_acceptance.py`

```python
class TestPhase1Acceptance:
    def test_all_28_letters_have_registry_rows(self):
        """Every Arabic letter exists in the letter registry."""

    def test_all_binary_roots_have_registry_rows(self):
        """Every binary root from Muajam exists in the binary registry."""

    def test_every_canonical_gloss_has_provenance(self):
        """No gloss value exists without at least one source entry."""

    def test_contested_entries_preserve_multiple_sources(self):
        """Entries with disagreeing scholars keep all claims, not force-merged."""

    def test_h2_outputs_link_to_binary_entries(self):
        """Promoted H2 coherence scores attach to binary registry entries."""
```

---

## Phase 2 — Build The Import System

### Task 2.1 — Import Validators

**File:** `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/canon_import.py`

```python
def validate_letter_import(rows: list[dict]) -> ImportReport:
    """Validate letter semantic entries before ingestion."""

def validate_binary_field_import(rows: list[dict]) -> ImportReport:
    """Validate binary field entries before ingestion."""

def validate_theory_claim_import(rows: list[dict]) -> ImportReport:
    """Validate theory claims before ingestion."""

def ingest_from_inbox(inbox_path: Path, registry_path: Path) -> ImportReport:
    """Main entry: validate all files in inbox, ingest valid ones, move to imported/."""
```

### Task 2.2 — Merge Policy

Rules implemented in code:
- `empty` → can be filled by `draft` or `curated`
- `draft` → can be upgraded by `curated`
- `curated` → cannot be overwritten silently (requires `force=True`)
- `promoted` → requires explicit replacement mode
- Conflicting scholar claims stored as parallel `sources[]`, never collapsed

### Task 2.3 — Import Report

Every import generates a JSON report:
```json
{
  "timestamp": "...",
  "source_folder": "inbox/letters/",
  "rows_added": 12,
  "rows_updated": 3,
  "rows_rejected": 1,
  "conflicts_found": 2,
  "missing_provenance": 0,
  "normalization_fixes": 4
}
```

### Task 2.4 — Import CLI

**Script:** `scripts/canon/import_theory_content.py`

```bash
python scripts/canon/import_theory_content.py --inbox data/theory_canon/inbox/ --registry data/theory_canon/
```

---

## Phase 3 — Build The Processing Pipeline

### Task 3.1 — Core Processing Contract

**File:** `Juthoor-ArabicGenome-LV1/src/juthoor_arabicgenome_lv1/core/canon_pipeline.py`

The 8-step pipeline:

```python
def process_root(root: str, registries: CanonRegistries) -> RootAnalysis:
    """
    1. normalize root/lemma
    2. resolve canonical structural identity
    3. resolve any available curated semantic content
    4. resolve binary field data
    5. resolve positional profile
    6. build composition attempt
    7. compare with observed lexical meaning
    8. return RootAnalysis with resolution status
    """
```

`RootAnalysis` includes:
- `resolution_status`: `resolved | partially_resolved | underdescribed | conflicted`
- All available semantic layers (conceptual, binary, positional, compositional)
- Explicit markers for what's missing

### Task 3.2 — Graceful Degradation

The pipeline MUST NOT crash on missing content:
- No letter gloss → `letter_trace.status = "underdescribed"`
- No binary field gloss → structural binary root preserved, semantic interpretation marked unresolved
- No Quranic contrast set → profile emitted without contrast analysis
- Every output clearly marks what data was available vs what was missing

### Task 3.3 — Pipeline Tests

Test with:
- Fully populated root → `resolved`
- Root with missing letter gloss → `partially_resolved`
- Root with no binary field data → `underdescribed`
- Root with conflicting sources → `conflicted`

---

## Phase 4 — Attach Research Factory Outputs

### Task 4.1 — Wire Existing Promotions

| Research Output | Attaches To | As |
|----------------|-------------|-----|
| H2 field coherence scores (396) | Binary Field Registry | `coherence_score` |
| H5 metathesis pairs (166) | Binary Field Registry | evidence attachment |
| H8 positional profiles (28) | Letter Semantics + Root Composition | `position_profile` |
| H10 partial compositionality | Root Composition Registry | `compositional_signal` (partial) |
| H9 negative result | Theory Claim Registry | `status: rejected` |

### Task 4.2 — Promotion Policy

Research results **validate or weaken** theory content. They do NOT substitute for curated glosses.

- Coherence > 0.6 + cross-lingual replication → can promote a binary field entry
- 2+ scholars agree on letter gloss direction → can promote a letter entry
- Kruskal-Wallis p < 0.01 → can promote a positional profile
- H10 remains `partial_signal`, not promoted as full compositionality

---

## Phase 5 — Quranic Interpretation Bridge

### Task 5.1 — QCA Output Contracts

Expose machine-readable evidence objects for QCA/LV3:
- `QuranicSemanticProfile`
- `InterpretationEvidenceCard`
- `ContrastPair`
- `ContextConstraintSet`

### Task 5.2 — Three-Layer Semantic Output

Every Quranic lemma profile MUST separate:
1. **Conceptual meaning** — root-level, abstract, stable
2. **Lexical realization** — what this form expresses
3. **Contextual actualization** — what the verse/surah makes active

Never collapse these into a single `meaning_text` field.

### Task 5.3 — Interpretation Policy

- LV1 produces **evidence for interpretation**, not final tafsir
- Intentionality = theory assumption, not proven fact
- No-synonymy = contrastive analysis rule, not automatic validator
- Anti-deletion / anti-reordering = methodological claims, stored with provenance

---

## Test Plan Summary

| Category | What | Count |
|----------|------|-------|
| Canon models | Dataclass instantiation, validation, immutability | ~15 |
| Canon loaders | Load/empty/malformed JSONL handling | ~12 |
| Seed script | Migration from current data, all 28 letters populated | ~8 |
| Import system | Validate, merge policy, status transitions, reports | ~15 |
| Processing pipeline | Full/partial/missing/conflicted resolution | ~10 |
| Research attachment | H2/H5/H8/H10/H9 wire correctly to registries | ~8 |
| Quranic bridge | Profile generation, layer separation, missing data handling | ~8 |
| **Total new tests** | | **~76** |

All 227 existing LV1 tests must continue to pass.

---

## Existing Architecture Preserved

```
core/           ← models.py stays, canon_models.py added alongside
                ← loaders.py stays, canon_loaders.py added alongside
factory/        ← experiment_runner.py, feature_store.py, promotions.py stay
scripts/        ← research_factory/ stays, canon/ added
data/           ← muajam/ stays, theory_canon/ added
outputs/        ← genome_v2/ stays, research_factory/ stays
tests/          ← all existing tests stay, canon tests added
```

No files deleted. No imports broken. Pure addition.

---

## Quality Gates

1. All 227 existing LV1 tests pass after every phase
2. No registry value without provenance
3. No forced consensus where scholars disagree
4. Pipeline degrades gracefully on missing content
5. Import system rejects malformed input with clear errors
6. Promoted values cannot be silently overwritten

---

*LV1 Core Restructure — Structure First, Content Later*
*Juthoor Linguistic Genealogy*
*2026-03-18*
