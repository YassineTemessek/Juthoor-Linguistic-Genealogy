"""Multi-language Arabic cognate discovery.

Runs phonetic-based discovery for multiple language pairs:
- ara<->heb  (Semitic<->Semitic, uses Hebrew IPA/translit + genome bonus)
- ara<->lat  (Semitic<->Latin, same phonetic pipeline as ara<->eng)

For each pair:
1. Load Arabic source (quran_lemmas_enriched, sample 500)
2. Load target corpus from LV0 kaikki.jsonl (Hebrew or Latin)
3. Score all pairs: PhoneticLawScorer + cross_lingual_skeleton_score
4. Evaluate against gold benchmarks (cognate_gold.jsonl + beyond_name_latin_pairs.jsonl)
5. Print comparison table alongside ara<->eng baseline

Hebrew notes:
- Hebrew entries have IPA or translit fields (latin-script) for phonetic comparison
- genome_scoring._LETTER_CLASS maps Arabic+Hebrew letters to shared class codes
- For Semitic<->Semitic pairs, add a genome bonus based on shared consonant class traces
"""
from __future__ import annotations

import heapq
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
LV2_ROOT = REPO_ROOT / "Juthoor-CognateDiscovery-LV2"
LV0_ROOT = REPO_ROOT / "Juthoor-DataCore-LV0"

ARABIC_CORPUS = LV2_ROOT / "data/processed/arabic/quran_lemmas_enriched.jsonl"

HEBREW_CORPUS = LV0_ROOT / "data/processed/hebrew/sources/kaikki.jsonl"
LATIN_CORPUS = LV0_ROOT / "data/processed/latin/classical/sources/kaikki.jsonl"

GOLD_BENCHMARK = LV2_ROOT / "resources/benchmarks/cognate_gold.jsonl"
LATIN_GOLD = LV2_ROOT / "data/processed/beyond_name_latin_pairs.jsonl"

ARABIC_LIMIT = 500
HEBREW_LIMIT = 5000   # all 17K; filter to those with IPA or usable translit
LATIN_LIMIT = 3000

TOP_K = 20

PHONETIC_WEIGHT = 0.6
SKELETON_WEIGHT = 0.4

# ---------------------------------------------------------------------------
# Package imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(LV2_ROOT / "src"))

from juthoor_cognatediscovery_lv2.discovery.phonetic_law_scorer import (
    PhoneticLawScorer,
    _arabic_consonant_skeleton,
    _english_consonant_skeleton,
    _strip_diacriticals,
    _pairwise_swap_variants,
    _morpheme_decompose,
    LATIN_EQUIVALENTS,
    normalize_arabic_root,
    project_root_sound_laws,
    _HIGH_FREQ_WORDS,
    _KNOWN_PREFIXES,
    _KNOWN_SUFFIXES,
)
from juthoor_cognatediscovery_lv2.discovery.correspondence import (
    cross_lingual_skeleton_score,
    correspondence_string,
)
from juthoor_cognatediscovery_lv2.discovery.phonetic_mergers import (
    merger_overlap,
    build_target_to_arabic_map,
    arabic_letter_set,
    load_phonetic_mergers,
)

# ---------------------------------------------------------------------------
# Arabic normalization
# ---------------------------------------------------------------------------
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_HAMZA_TR = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ئ": "ي", "ء": "ا"}
)


def _norm_arabic(text: str) -> str:
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(_HAMZA_TR)
    return text.strip()


# ---------------------------------------------------------------------------
# Hebrew/Semitic consonant class mapping (from genome_scoring._LETTER_CLASS)
# Used for Semitic<->Semitic genome bonus
# ---------------------------------------------------------------------------
_SEMITIC_CLASS = {
    # Arabic
    "ا": "ʔ", "ء": "ʔ", "أ": "ʔ", "إ": "ʔ", "آ": "ʔ", "ٱ": "ʔ",
    "ب": "b", "ت": "t", "ث": "s", "ج": "g", "ح": "ḥ", "خ": "ḫ",
    "د": "d", "ذ": "z", "ر": "r", "ز": "z", "س": "s", "ش": "s",
    "ص": "ṣ", "ض": "ḍ", "ط": "ṭ", "ظ": "ẓ", "ع": "ʕ", "غ": "ġ",
    "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
    "ه": "h", "و": "w", "ي": "y", "ى": "y",
    # Hebrew
    "א": "ʔ", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "w",
    "ז": "z", "ח": "ḥ", "ט": "t", "י": "y", "כ": "ḫ", "ך": "ḫ",
    "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
    "ע": "ʕ", "פ": "f", "ף": "f", "צ": "ṣ", "ץ": "ṣ", "ק": "q",
    "ר": "r", "ש": "s", "ת": "t",
}

_HEBREW_DIACRITICS_RE = re.compile(r"[\u05B0-\u05C7\uFB1D-\uFB4E]")


def _norm_hebrew_lemma(text: str) -> str:
    """Strip Hebrew diacritics/niqqud and return bare consonants."""
    text = _HEBREW_DIACRITICS_RE.sub("", text)
    return text.strip()


def _hebrew_semitic_class_string(text: str) -> str:
    """Map Hebrew/Arabic consonants to shared Semitic class codes."""
    text = _norm_hebrew_lemma(_norm_arabic(text))
    return "".join(_SEMITIC_CLASS.get(ch, "") for ch in text)


def _semitic_genome_score(arabic_text: str, hebrew_lemma: str) -> float:
    """Score Semitic correspondence via shared consonant class trace."""
    ara_cls = _hebrew_semitic_class_string(arabic_text)
    heb_cls = _hebrew_semitic_class_string(hebrew_lemma)
    if not ara_cls or not heb_cls:
        return 0.0
    return SequenceMatcher(None, ara_cls, heb_cls).ratio()


# ---------------------------------------------------------------------------
# IPA skeleton helper (reused from lightweight script)
# ---------------------------------------------------------------------------
_IPA_TO_LATIN_TR = str.maketrans(
    {
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    }
)
_IPA_VOWELS_RE = re.compile(r"[aeiouɪɛæʌɒɔʊəɑɜɐɵøœɶɯɤɨʉˈˌːʔ̃]")
_IPA_CONS_RE = re.compile(r"[bcdfghjklmnpqrstvwxyzðθɹɾʁχħʕɣβɸʔɫŋ]")


def _ipa_consonant_skeleton_fast(ipa: str) -> str:
    if not ipa:
        return ""
    s = ipa.lower()
    s = s.replace("tʃ", "c").replace("dʒ", "j").replace("ʃ", "sh").replace("ŋ", "ng")
    s = s.translate(_IPA_TO_LATIN_TR)
    return "".join(_IPA_CONS_RE.findall(s))


# ---------------------------------------------------------------------------
# Pre-computed per-Arabic structures
# ---------------------------------------------------------------------------

def _precompute_arabic(arabic_root: str) -> dict[str, Any]:
    ar_skel = _arabic_consonant_skeleton(arabic_root)
    primary_latin = _strip_diacriticals(
        "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
    )
    all_variants = project_root_sound_laws(arabic_root, include_group_expansion=True, max_variants=256)
    seen: dict[str, None] = {primary_latin: None}
    for v in all_variants:
        if v not in seen:
            seen[v] = None
        if len(seen) >= 8:
            break
    variants = tuple(seen.keys())
    meta_variants = (
        ([primary_latin[::-1]] + _pairwise_swap_variants(primary_latin)[:2])
        if primary_latin else []
    )
    corr_str = correspondence_string(arabic_root)
    ara_letters = arabic_letter_set(arabic_root)
    return {
        "ar_skel": ar_skel,
        "primary_latin": primary_latin,
        "variants": variants,
        "meta_variants": meta_variants,
        "corr_str": corr_str,
        "ara_letters": ara_letters,
        "raw": arabic_root,
    }


# ---------------------------------------------------------------------------
# Pre-computed per-target structures (generalized for any Latin-script target)
# ---------------------------------------------------------------------------

def _precompute_target_batch(
    target_entries: list[dict[str, Any]],
    lang: str,
) -> list[dict[str, Any]]:
    """Pre-compute scoring structures for target entries.

    For Hebrew: uses IPA-derived Latin skeleton + Hebrew lemma for genome score.
    For Latin: uses lemma directly (already Latin script) + IPA.
    Both share the same scoring pipeline as English targets.
    """
    results = []
    for tgt in target_entries:
        lemma = str(tgt.get("lemma") or "").strip()
        ipa = str(tgt.get("ipa") or "").strip()

        if lang == "heb":
            # Hebrew lemma is in Hebrew script; use translit or IPA for Latin-based scoring
            translit = str(tgt.get("translit") or "").strip()
            # IPA is more reliable for consonant extraction
            if ipa:
                # Strip IPA brackets/slashes
                ipa_clean = re.sub(r"[/\[\]()ˈˌ]", "", ipa).strip()
                latin_form = ipa_clean
            elif translit and all(ord(c) < 0x0600 for c in translit):
                # translit in Hebrew script — not useful for Latin skeleton
                # Use empty; will rely on genome score only
                latin_form = ""
            else:
                latin_form = ""
            target_skel = _english_consonant_skeleton(latin_form) if latin_form else ""
            ipa_skel = _ipa_consonant_skeleton_fast(ipa) if ipa else ""
            corr_str = correspondence_string(latin_form) if latin_form else ""
            _, stem, suffix = _morpheme_decompose(latin_form) if latin_form else ("", "", "")
            stem_skel = _english_consonant_skeleton(stem) if stem and len(stem) >= 2 else ""
            is_high_freq = False
        else:
            # Latin, Greek, etc. — lemma is already Latin script
            latin_form = lemma.lower()
            target_skel = _english_consonant_skeleton(latin_form)
            ipa_skel = _ipa_consonant_skeleton_fast(ipa) if ipa else ""
            corr_str = correspondence_string(latin_form)
            _, stem, suffix = _morpheme_decompose(latin_form)
            stem_skel = _english_consonant_skeleton(stem) if (suffix or _) and stem and len(stem) >= 2 else ""
            is_high_freq = latin_form in _HIGH_FREQ_WORDS

        results.append({
            "entry": tgt,
            "lemma": lemma,
            "latin_form": latin_form,
            "target_skel": target_skel,
            "ipa_skel": ipa_skel,
            "corr_str": corr_str,
            "stem_skel": stem_skel,
            "is_high_freq": is_high_freq,
            "lang": lang,
        })
    return results


# ---------------------------------------------------------------------------
# Merger map (pre-built for speed)
# ---------------------------------------------------------------------------
_ENG_MERGER_RULES = load_phonetic_mergers()
_ENG_MERGER_MAP: dict[str, set[str]] = build_target_to_arabic_map("eng", rules=_ENG_MERGER_RULES)


def _merger_overlap_fast(ara_letters: set[str], target_latin: str) -> set[str]:
    tgt: set[str] = set()
    for ch in target_latin:
        if ch in _ENG_MERGER_MAP:
            tgt.update(_ENG_MERGER_MAP[ch])
    return ara_letters & tgt


# ---------------------------------------------------------------------------
# Fast scoring
# ---------------------------------------------------------------------------
_IPA_LATIN_MAP = str.maketrans(
    {
        "θ": "s", "ð": "d", "ɹ": "r", "ɾ": "r", "ʁ": "r",
        "χ": "kh", "ħ": "h", "ʕ": "", "ɣ": "g", "β": "b",
        "ɸ": "f", "ʔ": "", "ɫ": "l", "ʍ": "wh",
    }
)


def _score_fast(
    ara_pre: dict[str, Any],
    tgt_pre: dict[str, Any],
    scorer: PhoneticLawScorer,
    semitic_pair: bool = False,
) -> float:
    """Fast combined score using pre-computed structures.

    For Semitic pairs (ara↔heb), adds genome_score based on shared consonant classes.
    """
    ar_skel = ara_pre["ar_skel"]
    primary_latin = ara_pre["primary_latin"]
    variants = ara_pre["variants"]
    meta_variants = ara_pre["meta_variants"]
    ara_corr = ara_pre["corr_str"]

    tgt_skel = tgt_pre["target_skel"]
    ipa_skel = tgt_pre["ipa_skel"]
    tgt_corr = tgt_pre["corr_str"]
    stem_skel = tgt_pre["stem_skel"]
    is_high_freq = tgt_pre["is_high_freq"]
    latin_form = tgt_pre["latin_form"]
    lang = tgt_pre["lang"]

    # For Hebrew without IPA, rely entirely on genome score
    if not ar_skel or len(ar_skel) < 2:
        return 0.0

    # Genome bonus for Semitic↔Semitic pairs (before phonetic check)
    genome_bonus = 0.0
    if semitic_pair:
        genome_bonus = _semitic_genome_score(ara_pre["raw"], tgt_pre["lemma"]) * 0.35

    # If no Latin form for target (Hebrew without IPA/translit), use only genome
    if not tgt_skel and not ipa_skel:
        if semitic_pair and genome_bonus > 0:
            return min(round(genome_bonus, 6), 1.0)
        return 0.0

    if len(tgt_skel) < 2:
        # Still try genome if available
        if semitic_pair and genome_bonus > 0.3:
            return min(round(genome_bonus * 0.7, 6), 1.0)
        return 0.0

    # Length ratio guard
    ratio = len(tgt_skel) / len(ar_skel) if ar_skel else 0.0
    if ratio > 4.0 or ratio < 0.25:
        if semitic_pair and genome_bonus > 0.4:
            return min(round(genome_bonus * 0.6, 6), 1.0)
        return 0.0

    # Projection match
    proj_score = 0.0
    for var in variants:
        clean = _strip_diacriticals(var)
        s = SequenceMatcher(None, clean, tgt_skel).ratio()
        if s > proj_score:
            proj_score = s

    # Direct match
    direct_score = (
        SequenceMatcher(None, primary_latin, tgt_skel).ratio()
        if primary_latin and tgt_skel else 0.0
    )

    # IPA match
    ipa_proj_score = 0.0
    if ipa_skel:
        ipa_lat = ipa_skel.replace("tʃ", "ch").replace("dʒ", "j")
        ipa_lat = ipa_lat.replace("ʃ", "sh").replace("ʒ", "zh").replace("ŋ", "ng")
        ipa_lat = ipa_lat.translate(_IPA_LATIN_MAP)
        for var in variants:
            clean = _strip_diacriticals(var)
            s = SequenceMatcher(None, clean, ipa_lat).ratio()
            if s > ipa_proj_score:
                ipa_proj_score = s

    # Metathesis
    metathesis_score = 0.0
    if primary_latin and tgt_skel:
        for mv in meta_variants:
            s = SequenceMatcher(None, mv, tgt_skel).ratio()
            if s > metathesis_score:
                metathesis_score = s

    # Stem score
    stem_score = 0.0
    if stem_skel:
        stem_proj = max(
            (SequenceMatcher(None, _strip_diacriticals(v), stem_skel).ratio() for v in variants),
            default=0.0,
        )
        stem_direct = (
            SequenceMatcher(None, primary_latin, stem_skel).ratio()
            if primary_latin and stem_skel else 0.0
        )
        stem_score = max(stem_proj, stem_direct)

    base_score = max(proj_score, direct_score, stem_score, ipa_proj_score)
    phonetic = base_score + min(metathesis_score * 0.4, 0.12)
    phonetic = min(phonetic, 1.0)

    if is_high_freq:
        phonetic *= 0.6

    # Skeleton (correspondence class similarity)
    skeleton = (
        SequenceMatcher(None, ara_corr, tgt_corr).ratio()
        if ara_corr and tgt_corr else 0.0
    )

    # Merger overlap bonus
    overlap = _merger_overlap_fast(ara_pre.get("ara_letters", set()), latin_form)
    merger_bonus = min(len(overlap) * 0.02, 0.10)

    combined = PHONETIC_WEIGHT * phonetic + SKELETON_WEIGHT * skeleton + merger_bonus
    # Add genome bonus for Semitic pairs on top of phonetic/skeleton
    combined = combined + genome_bonus
    return min(round(combined, 6), 1.0)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_arabic_entries(path: Path, limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            root = rec.get("root", "")
            lemma = rec.get("lemma", "")
            pos = rec.get("pos_tag", "")
            if not root or len(lemma.strip()) < 2:
                continue
            if pos in {"P", ""}:
                continue
            entries.append(rec)
            if len(entries) >= limit:
                break
    return entries


def _load_target_entries(path: Path, limit: int, lang: str) -> list[dict[str, Any]]:
    """Load target-language entries from LV0 kaikki.jsonl."""
    entries: list[dict[str, Any]] = []
    seen_lemmas: set[str] = set()

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            lemma = str(rec.get("lemma") or "").strip()
            if not lemma or len(lemma) < 2:
                continue
            lemma_lower = lemma.lower()
            if lemma_lower in seen_lemmas:
                continue

            if lang == "heb":
                # Accept Hebrew entries with IPA or at least a Hebrew lemma
                ipa = str(rec.get("ipa") or "").strip()
                # Skip entries that are just English glosses or pure Latin
                if not any("\u05D0" <= c <= "\u05EA" for c in lemma):
                    continue  # not Hebrew script
                seen_lemmas.add(lemma_lower)
                entries.append(rec)
            elif lang == "lat":
                # Latin: require IPA and Latin-only lemma
                ipa = str(rec.get("ipa") or "").strip()
                if not ipa:
                    continue
                if not lemma.replace("-", "").replace("'", "").isalpha():
                    continue
                if not lemma.isascii():
                    continue
                seen_lemmas.add(lemma_lower)
                entries.append(rec)

            if len(entries) >= limit:
                break

    return entries


# ---------------------------------------------------------------------------
# Gold benchmark loaders
# ---------------------------------------------------------------------------

def _load_gold_pairs_semitic(path: Path, tgt_lang: str) -> dict[str, set[str]]:
    """Load gold pairs from cognate_gold.jsonl for a specific target language."""
    gold: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            if src.get("lang") == "ara" and tgt.get("lang") == tgt_lang:
                ara_l = _norm_arabic(str(src.get("lemma", "")))
                tgt_l = str(tgt.get("lemma", "")).strip()
                if ara_l and tgt_l:
                    gold.setdefault(ara_l, set()).add(tgt_l)
    return gold


def _load_gold_pairs_latin(path: Path) -> dict[str, set[str]]:
    """Load gold pairs from beyond_name_latin_pairs.jsonl."""
    gold: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            src = rec.get("source", {})
            tgt = rec.get("target", {})
            if src.get("lang") == "ara" and tgt.get("lang") == "lat":
                ara_l = _norm_arabic(str(src.get("lemma", "")))
                lat_l = str(tgt.get("lemma", "")).strip().lower()
                if ara_l and lat_l:
                    gold.setdefault(ara_l, set()).add(lat_l)
    return gold


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def run_discovery(
    arabic_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
    target_lang: str,
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    scorer = PhoneticLawScorer()
    semitic_pair = target_lang in {"heb", "arc"}

    print(f"  Pre-computing {target_lang} target features ({len(target_entries)} entries)...", flush=True)
    tgt_pre_list = _precompute_target_batch(target_entries, lang=target_lang)
    print(f"  Done. Starting scoring loop ({len(arabic_entries)} Arabic entries)...", flush=True)

    leads: list[dict[str, Any]] = []
    total = len(arabic_entries)

    for i, ara in enumerate(arabic_entries):
        if i % 50 == 0:
            print(f"  [{i}/{total}] Arabic entries scored...", flush=True)

        ara_lemma = str(ara.get("lemma", "")).strip()
        ara_root = str(ara.get("root") or "").strip()
        ara_gloss = str(ara.get("gloss") or "").strip()
        ara_translit = str(ara.get("translit") or "").strip()
        ara_pre = _precompute_arabic(ara_root or ara_lemma)

        pair_scores: list[tuple[float, int]] = []
        for j, tgt_pre in enumerate(tgt_pre_list):
            combined = _score_fast(ara_pre, tgt_pre, scorer, semitic_pair=semitic_pair)
            if combined > 0.0:
                pair_scores.append((combined, j))

        top = heapq.nlargest(top_k, pair_scores, key=lambda x: x[0])

        for rank, (combined, j) in enumerate(top):
            tgt_pre = tgt_pre_list[j]
            tgt = tgt_pre["entry"]
            tgt_lemma = tgt_pre["lemma"]
            tgt_latin = tgt_pre["latin_form"]
            tgt_ipa = str(tgt.get("ipa", "")).strip()
            tgt_gloss = str(tgt.get("gloss_plain") or tgt.get("gloss") or "").strip()

            overlap = _merger_overlap_fast(ara_pre["ara_letters"], tgt_latin)

            leads.append({
                "source_lemma": ara_lemma,
                "source_lemma_norm": _norm_arabic(ara_lemma),
                "source_root": ara_root,
                "source_gloss": ara_gloss,
                "source_translit": ara_translit,
                "target_lemma": tgt_lemma,
                "target_latin": tgt_latin,
                "target_ipa": tgt_ipa,
                "target_gloss": tgt_gloss,
                "combined_score": combined,
                "rank": rank + 1,
                "target_lang": target_lang,
                "merger_overlap": list(overlap),
            })

    return leads


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_vs_gold(
    leads: list[dict[str, Any]],
    gold: dict[str, set[str]],
    top_ks: tuple[int, ...] = (1, 5, 10, 20),
) -> dict[str, Any]:
    leads_index: dict[str, list[tuple[int, str]]] = {}
    for lead in leads:
        src = lead.get("source_lemma_norm") or _norm_arabic(lead["source_lemma"])
        leads_index.setdefault(src, []).append((lead["rank"], lead["target_lemma"]))

    reciprocal_ranks: list[float] = []
    hits: dict[int, list[int]] = {k: [] for k in top_ks}
    evaluated = 0

    for ara_lemma, tgt_targets in gold.items():
        if ara_lemma not in leads_index:
            continue
        ranked_targets = sorted(leads_index[ara_lemma], key=lambda x: x[0])
        target_set = {t.lower() for t in tgt_targets}

        found_rank = None
        for rank, tgt_lemma in ranked_targets:
            if tgt_lemma.lower() in target_set:
                found_rank = rank
                break

        reciprocal_ranks.append(1.0 / found_rank if found_rank else 0.0)
        for k in top_ks:
            top_k_targets = {t for r, t in ranked_targets if r <= k}
            hits[k].append(1 if target_set & top_k_targets else 0)
        evaluated += 1

    if not evaluated:
        return {"evaluated_queries": 0, "mrr": 0.0, **{f"hit@{k}": 0.0 for k in top_ks}}

    result: dict[str, Any] = {
        "evaluated_queries": evaluated,
        "mrr": round(sum(reciprocal_ranks) / evaluated, 4),
    }
    for k in top_ks:
        result[f"hit@{k}"] = round(sum(hits[k]) / evaluated, 4)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    print("=== Multi-Language Arabic Cognate Discovery ===")
    print(f"Timestamp: {timestamp}\n")

    # Load Arabic source (shared across all pairs)
    print(f"Loading Arabic corpus (limit={ARABIC_LIMIT})...")
    arabic_entries = _load_arabic_entries(ARABIC_CORPUS, ARABIC_LIMIT)
    print(f"  Loaded {len(arabic_entries)} Arabic content entries\n")

    results: dict[str, dict[str, Any]] = {}

    # --- ara <-> heb ---
    print("=" * 60)
    print("PAIR: ara <-> heb")
    print("=" * 60)
    print(f"Loading Hebrew corpus (limit={HEBREW_LIMIT})...")
    heb_entries = _load_target_entries(HEBREW_CORPUS, HEBREW_LIMIT, lang="heb")
    print(f"  Loaded {len(heb_entries)} Hebrew entries")
    ipa_count = sum(1 for e in heb_entries if e.get("ipa"))
    print(f"  Of which {ipa_count} have IPA ({ipa_count/len(heb_entries)*100:.1f}%)")

    print("Loading Hebrew gold benchmark...")
    heb_gold = _load_gold_pairs_semitic(GOLD_BENCHMARK, tgt_lang="heb")
    print(f"  Loaded {len(heb_gold)} query lemmas ({sum(len(v) for v in heb_gold.values())} total pairs)")

    print(f"\nScoring {len(arabic_entries)} x {len(heb_entries)} pairs...")
    heb_leads = run_discovery(arabic_entries, heb_entries, target_lang="heb", top_k=TOP_K)
    print(f"  Generated {len(heb_leads)} lead pairs")

    print("Evaluating...")
    heb_metrics = evaluate_vs_gold(heb_leads, heb_gold)
    results["ara<->heb"] = {
        "metrics": heb_metrics,
        "gold_pairs": sum(len(v) for v in heb_gold.values()),
        "target_size": len(heb_entries),
        "leads": heb_leads,
        "gold": heb_gold,
    }
    print(f"  ara<->heb MRR={heb_metrics['mrr']:.4f}  "
          f"H@1={heb_metrics.get('hit@1',0):.4f}  "
          f"H@5={heb_metrics.get('hit@5',0):.4f}  "
          f"H@10={heb_metrics.get('hit@10',0):.4f}")

    # --- ara <-> lat ---
    print("\n" + "=" * 60)
    print("PAIR: ara <-> lat")
    print("=" * 60)
    print(f"Loading Latin corpus (limit={LATIN_LIMIT})...")
    lat_entries = _load_target_entries(LATIN_CORPUS, LATIN_LIMIT, lang="lat")
    print(f"  Loaded {len(lat_entries)} Latin entries (with IPA)")

    print("Loading Latin gold benchmark...")
    lat_gold = _load_gold_pairs_latin(LATIN_GOLD)
    print(f"  Loaded {len(lat_gold)} query lemmas ({sum(len(v) for v in lat_gold.values())} total pairs)")

    print(f"\nScoring {len(arabic_entries)} x {len(lat_entries)} pairs...")
    lat_leads = run_discovery(arabic_entries, lat_entries, target_lang="lat", top_k=TOP_K)
    print(f"  Generated {len(lat_leads)} lead pairs")

    print("Evaluating...")
    lat_metrics = evaluate_vs_gold(lat_leads, lat_gold)
    results["ara<->lat"] = {
        "metrics": lat_metrics,
        "gold_pairs": sum(len(v) for v in lat_gold.values()),
        "target_size": len(lat_entries),
        "leads": lat_leads,
        "gold": lat_gold,
    }
    print(f"  ara<->lat MRR={lat_metrics['mrr']:.4f}  "
          f"H@1={lat_metrics.get('hit@1',0):.4f}  "
          f"H@5={lat_metrics.get('hit@5',0):.4f}  "
          f"H@10={lat_metrics.get('hit@10',0):.4f}")

    # ---------------------------------------------------------------------------
    # Comparison table
    # ara<->eng baseline from last run
    # ---------------------------------------------------------------------------
    ARA_ENG_PAIRS = 775   # gold pairs count from beyond_name_cognate_gold_candidates.jsonl (ara<->eng)
    ARA_ENG_MRR = 0.0385
    ARA_ENG_H1 = 0.0385
    ARA_ENG_H5 = 0.0385
    ARA_ENG_H10 = 0.0385

    hm = heb_metrics
    lm = lat_metrics

    print("\n")
    print("=" * 65)
    print("=== MULTI-LANGUAGE DISCOVERY COMPARISON ===")
    print("=" * 65)
    print(f"{'':20s} | {'ara<->eng':>10s} | {'ara<->heb':>10s} | {'ara<->lat':>10s} |")
    print("-" * 65)
    print(f"{'Gold pairs':20s} | {ARA_ENG_PAIRS:>10d} | {sum(len(v) for v in heb_gold.values()):>10d} | {sum(len(v) for v in lat_gold.values()):>10d} |")
    print(f"{'Queries evaluated':20s} | {'26':>10s} | {int(hm['evaluated_queries']):>10d} | {int(lm['evaluated_queries']):>10d} |")
    print(f"{'MRR':20s} | {ARA_ENG_MRR:>10.4f} | {hm['mrr']:>10.4f} | {lm['mrr']:>10.4f} |")
    print(f"{'Hit@1':20s} | {ARA_ENG_H1*100:>9.1f}% | {hm.get('hit@1',0)*100:>9.1f}% | {lm.get('hit@1',0)*100:>9.1f}% |")
    print(f"{'Hit@5':20s} | {ARA_ENG_H5*100:>9.1f}% | {hm.get('hit@5',0)*100:>9.1f}% | {lm.get('hit@5',0)*100:>9.1f}% |")
    print(f"{'Hit@10':20s} | {ARA_ENG_H10*100:>9.1f}% | {hm.get('hit@10',0)*100:>9.1f}% | {lm.get('hit@10',0)*100:>9.1f}% |")
    print("=" * 65)

    # ---------------------------------------------------------------------------
    # Top discoveries per pair (not in gold)
    # ---------------------------------------------------------------------------
    for pair_name, pair_data in results.items():
        leads = pair_data["leads"]
        gold = pair_data["gold"]
        gold_set: set[tuple[str, str]] = set()
        for ara_l, tgt_set in gold.items():
            for tgt_l in tgt_set:
                gold_set.add((ara_l, tgt_l.lower()))

        novel = []
        for lead in leads:
            norm_src = lead.get("source_lemma_norm") or _norm_arabic(lead["source_lemma"])
            key = (norm_src, lead["target_lemma"].lower())
            if key not in gold_set:
                novel.append(lead)
        novel.sort(key=lambda x: (-x["combined_score"], x["rank"]))
        novel = novel[:20]

        print(f"\n=== TOP NEW DISCOVERIES: {pair_name} ===")
        for i, lead in enumerate(novel[:10], 1):
            src_label = lead["source_lemma"]
            if lead["source_gloss"]:
                src_label += f" ({lead['source_gloss']})"
            elif lead["source_translit"]:
                src_label += f" [{lead['source_translit']}]"
            tgt_label = lead["target_lemma"]
            if lead["target_ipa"]:
                tgt_label += f" /{lead['target_ipa']}/"
            print(f"{i:3}. Arabic {src_label!r} -> {pair_name.split('<->')[1].upper()} {tgt_label!r}")
            print(f"     score={lead['combined_score']:.4f}  rank={lead['rank']}")

    # Save leads
    leads_dir = LV2_ROOT / "outputs/leads"
    leads_dir.mkdir(parents=True, exist_ok=True)
    for pair_name, pair_data in results.items():
        pair_slug = pair_name.replace("<->", "_")
        out_path = leads_dir / f"multilang_{pair_slug}_{timestamp}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for lead in pair_data["leads"]:
                f.write(json.dumps(lead, ensure_ascii=False) + "\n")
        print(f"\nLeads saved: {out_path}")


if __name__ == "__main__":
    main()
