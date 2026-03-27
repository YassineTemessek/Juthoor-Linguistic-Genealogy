"""Multi-method etymology scorer.

For each Arabic<->English candidate pair, runs all applicable linking methods
and returns the best score + which method(s) fired.

Methods implemented:
1. Direct consonant skeleton match
2. Morpheme decomposition (prefix + stem + suffix)
3. Multi-hop chain (via Latin/Greek intermediate)
4. Guttural-aware projection (Khashim laws)
5. Emphatic collapse scoring
6. Metathesis detection (consonant reversal)
7. Dialect variant matching
8. Position-weighted scoring (LV1 H8)
9. IPA-based scoring
10. Reverse root generation (English->possible Arabic roots)
11. Synonym family expansion
12. Article detection (al- absorption)
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .phonetic_law_scorer import (
    PhoneticLawScorer,
    _arabic_consonant_skeleton,
    _english_consonant_skeleton,
    _morpheme_decompose,
    _pairwise_swap_variants,
    _strip_diacriticals,
    _best_projection_match,
    _weighted_projection_score,
    _best_projection_match_ipa,
    LATIN_EQUIVALENTS,
    _KNOWN_PREFIXES,
    _KNOWN_SUFFIXES,
)

try:
    from juthoor_arabicgenome_lv1.factory.sound_laws import (
        normalize_arabic_root,
        project_root_by_target,
        project_root_sound_laws,
    )
except ImportError:
    from .phonetic_law_scorer import (  # type: ignore[assignment]
        normalize_arabic_root,  # type: ignore[attr-defined]
        project_root_by_target,  # type: ignore[attr-defined]
        project_root_sound_laws,  # type: ignore[attr-defined]
    )

from .phonetic_mergers import _ENGLISH_BASE_MAP

# ---------------------------------------------------------------------------
# Dialect shift tables
# ---------------------------------------------------------------------------

_DIALECT_SHIFTS: dict[str, dict[str, str]] = {
    "gulf": {"ج": "ي", "ق": "ج", "ك": "تش"},
    "egyptian": {"ج": "g", "ق": "ء", "ث": "س"},
    "moroccan": {"ق": "ء", "ث": "ت"},
}

# ---------------------------------------------------------------------------
# Intermediate-language consonant sets for multi-hop via Latin/Greek
# ---------------------------------------------------------------------------

_LATIN_CONSONANTS = set("bcdfghjklmnpqrstvwxyz")
_GREEK_TO_LATIN: dict[str, str] = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e",
    "ζ": "z", "η": "e", "θ": "th", "ι": "i", "κ": "k",
    "λ": "l", "μ": "m", "ν": "n", "ξ": "x", "ο": "o",
    "π": "p", "ρ": "r", "σ": "s", "τ": "t", "υ": "u",
    "φ": "ph", "χ": "kh", "ψ": "ps", "ω": "o",
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MethodResult:
    method_name: str
    score: float
    explanation: str
    arabic_variant_used: str
    english_variant_used: str


@dataclass
class MultiMethodScore:
    best_score: float
    best_method: str
    all_results: list[MethodResult]
    arabic_expansions_tried: int
    methods_that_fired: list[str]  # methods with score > 0.4


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

class MultiMethodScorer:
    def __init__(self) -> None:
        self._phonetic_scorer = PhoneticLawScorer()
        self._synonym_families: dict[str, list[str]] | None = None
        self._synonym_loaded: bool = False
        self._ipa_lookup: Any = None

    # ------------------------------------------------------------------
    # Lazy loaders
    # ------------------------------------------------------------------

    def _get_synonym_families(self) -> dict[str, list[str]]:
        if self._synonym_loaded:
            return self._synonym_families or {}
        self._synonym_loaded = True
        here = Path(__file__).resolve()
        repo_root = here.parents[4]
        families_path = (
            repo_root
            / "Juthoor-ArabicGenome-LV1"
            / "data"
            / "theory_canon"
            / "roots"
            / "synonym_families_full.jsonl"
        )
        if families_path.exists():
            from .synonym_expansion import load_synonym_families
            self._synonym_families = load_synonym_families(str(families_path))
        return self._synonym_families or {}

    def _get_ipa_lookup(self) -> Any:
        if self._ipa_lookup is None:
            from .ipa_lookup import IPALookup
            self._ipa_lookup = IPALookup()
        return self._ipa_lookup

    # ------------------------------------------------------------------
    # Arabic expansion
    # ------------------------------------------------------------------

    def _expand_arabic(self, root: str) -> list[str]:
        """Get all Arabic variants to try against English."""
        variants: list[str] = [root]

        # 1. Synonym family (up to 10)
        families = self._get_synonym_families()
        if families:
            from .synonym_expansion import expand_root
            variants.extend(expand_root(root, families)[:10])

        # 2. Dialect variants
        normalized = normalize_arabic_root(root)
        for _dialect, shifts in _DIALECT_SHIFTS.items():
            dialect_form = normalized
            for ar_letter, replacement in shifts.items():
                dialect_form = dialect_form.replace(ar_letter, replacement)
            if dialect_form != normalized:
                variants.append(dialect_form)

        # 3. Deduplicate, preserve order
        seen: set[str] = set()
        unique: list[str] = []
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                unique.append(v)
        return unique

    # ------------------------------------------------------------------
    # English decompositions
    # ------------------------------------------------------------------

    def _decompose_english(self, word: str) -> list[tuple[str, str, str]]:
        """Return list of (prefix, stem, suffix) decompositions."""
        w = word.lower().strip()
        results: list[tuple[str, str, str]] = [("", w, "")]  # always include full word

        # Try every prefix
        for p in sorted(_KNOWN_PREFIXES, key=len, reverse=True):
            if w.startswith(p) and len(w) > len(p) + 2:
                stem = w[len(p):]
                # Try every suffix on this stem
                for s in sorted(_KNOWN_SUFFIXES, key=len, reverse=True):
                    if stem.endswith(s) and len(stem) > len(s) + 1:
                        results.append((p, stem[: -len(s)], s))
                        break
                results.append((p, stem, ""))
                break

        # Try suffix-only
        for s in sorted(_KNOWN_SUFFIXES, key=len, reverse=True):
            if w.endswith(s) and len(w) > len(s) + 1:
                results.append(("", w[: -len(s)], s))
                break

        # Deduplicate
        seen: set[tuple[str, str, str]] = set()
        unique: list[tuple[str, str, str]] = []
        for t in results:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique

    # ------------------------------------------------------------------
    # Article detection
    # ------------------------------------------------------------------

    def _strip_article(self, word: str) -> list[str]:
        """Check for absorbed Arabic article al-."""
        w = word.lower()
        variants = [w]
        if w.startswith("al") and len(w) > 3:
            variants.append(w[2:])
        if w.startswith("a") and not w.startswith("al") and len(w) > 2:
            variants.append(w[1:])
        return variants

    # ------------------------------------------------------------------
    # Metathesis variants
    # ------------------------------------------------------------------

    def _metathesis_variants(self, skeleton: str) -> list[str]:
        """Generate all metathesis variants of a consonant skeleton."""
        variants = [skeleton[::-1]]  # full reversal
        variants.extend(_pairwise_swap_variants(skeleton))
        return variants

    # ------------------------------------------------------------------
    # Reverse root generation
    # ------------------------------------------------------------------

    def _reverse_generate_arabic(self, eng_skeleton: str) -> list[str]:
        """Given English consonant skeleton, generate possible Arabic roots.

        Returns up to 50 candidate Arabic root strings by mapping each English
        consonant back to possible Arabic letters via _ENGLISH_BASE_MAP.
        Only consonants found in the map are used; unknown chars are skipped.
        """
        options: list[list[str]] = []
        for ch in eng_skeleton.lower():
            if ch in _ENGLISH_BASE_MAP:
                options.append(sorted(_ENGLISH_BASE_MAP[ch]))
        if not options:
            return []
        candidates: list[str] = []
        for combo in itertools.product(*options):
            c = "".join(combo)
            if c and c not in candidates:
                candidates.append(c)
            if len(candidates) >= 50:
                break
        return candidates

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _score_skeleton_pair(self, ar_variant: str, eng_form: str) -> float:
        """Score a single Arabic variant string vs English form directly."""
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        eng_skel = _english_consonant_skeleton(eng_form)
        if not ar_skel or not eng_skel:
            return 0.0
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        direct = SequenceMatcher(None, primary_latin, eng_skel).ratio() if primary_latin else 0.0
        proj, _ = _best_projection_match(ar_variant, eng_form)
        return max(direct, proj)

    # ------------------------------------------------------------------
    # Individual methods
    # ------------------------------------------------------------------

    def _method_direct_skeleton(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        score = self._score_skeleton_pair(ar_variant, eng_form)
        if score <= 0.0:
            return None
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        eng_skel = _english_consonant_skeleton(eng_form)
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        return MethodResult(
            method_name="direct_skeleton",
            score=score,
            explanation=f"Arabic skeleton '{ar_skel}' projects to '{primary_latin}', matched '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_morpheme_decomposition(
        self, ar_variant: str, word: str
    ) -> list[MethodResult]:
        results: list[MethodResult] = []
        decomps = self._decompose_english(word)
        for prefix, stem, suffix in decomps:
            if not stem or stem == word.lower():
                continue  # skip full-word decomposition (handled by direct_skeleton)
            score = self._score_skeleton_pair(ar_variant, stem)
            if score <= 0.0:
                continue
            has_morpheme = bool(prefix or suffix)
            bonus = 0.05 if has_morpheme else 0.0
            final_score = min(score + bonus, 1.0)
            results.append(MethodResult(
                method_name="morpheme_decomposition",
                score=final_score,
                explanation=(
                    f"Stripped prefix='{prefix}' suffix='{suffix}', "
                    f"stem '{stem}' matched Arabic '{ar_variant}'"
                ),
                arabic_variant_used=ar_variant,
                english_variant_used=stem,
            ))
        return results

    def _method_multi_hop(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        """Score via Latin/Greek intermediate: project Arabic to Latin, then match."""
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        if not ar_skel:
            return None
        eng_skel = _english_consonant_skeleton(eng_form)
        if not eng_skel:
            return None
        # Use full sound-law projection (includes more variants = broader Latin search)
        try:
            variants = project_root_sound_laws(ar_variant, include_group_expansion=True, max_variants=128)
        except Exception:
            return None
        if not variants:
            return None
        best_score, best_var = 0.0, ""
        for var in variants:
            clean = _strip_diacriticals(var).lower()
            # Allow 1-character off by using partial matching via ratio
            ratio = SequenceMatcher(None, clean, eng_skel).ratio()
            if ratio > best_score:
                best_score, best_var = ratio, clean
        if best_score <= 0.0:
            return None
        return MethodResult(
            method_name="multi_hop_chain",
            score=best_score,
            explanation=f"Latin/Greek hop: '{ar_skel}' → '{best_var}' ↔ '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_guttural_projection(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        """Khashim guttural laws: ع/غ/ح/خ often deleted or become h/g in European."""
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        gutturals = set("عغحخ")
        if not any(ch in gutturals for ch in ar_skel):
            return None
        # Strip gutturals from Arabic skeleton and score the remainder
        stripped = "".join(ch for ch in ar_skel if ch not in gutturals)
        if not stripped:
            return None
        score = self._score_skeleton_pair(stripped, eng_form)
        if score <= 0.0:
            return None
        eng_skel = _english_consonant_skeleton(eng_form)
        return MethodResult(
            method_name="guttural_projection",
            score=score,
            explanation=f"Gutturals dropped: '{ar_skel}' → '{stripped}' ↔ '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_emphatic_collapse(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        """Arabic emphatics (ص ض ط ظ) collapse to their plain counterparts."""
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        _EMPHATIC_MAP = {"ص": "س", "ض": "د", "ط": "ت", "ظ": "ز"}
        if not any(ch in _EMPHATIC_MAP for ch in ar_skel):
            return None
        collapsed = "".join(_EMPHATIC_MAP.get(ch, ch) for ch in ar_skel)
        score = self._score_skeleton_pair(collapsed, eng_form)
        if score <= 0.0:
            return None
        eng_skel = _english_consonant_skeleton(eng_form)
        return MethodResult(
            method_name="emphatic_collapse",
            score=score,
            explanation=f"Emphatics collapsed: '{ar_skel}' → '{collapsed}' ↔ '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_metathesis(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        eng_skel = _english_consonant_skeleton(eng_form)
        if not ar_skel or not eng_skel:
            return None
        primary_latin = _strip_diacriticals(
            "".join(LATIN_EQUIVALENTS.get(ch, (ch,))[0] for ch in ar_skel)
        )
        if not primary_latin:
            return None
        best_score, best_meta = 0.0, ""
        for meta_var in self._metathesis_variants(primary_latin):
            score = SequenceMatcher(None, meta_var, eng_skel).ratio()
            if score > best_score:
                best_score, best_meta = score, meta_var
        if best_score <= 0.0:
            return None
        return MethodResult(
            method_name="metathesis",
            score=best_score,
            explanation=f"Metathesis variant '{best_meta}' matched '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_dialect_variant(
        self, ar_variant: str, eng_form: str, dialect: str
    ) -> MethodResult | None:
        score = self._score_skeleton_pair(ar_variant, eng_form)
        if score <= 0.0:
            return None
        return MethodResult(
            method_name=f"dialect_variant_{dialect}",
            score=score,
            explanation=f"Dialect ({dialect}) form '{ar_variant}' matched '{eng_form}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_position_weighted(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        eng_skel = _english_consonant_skeleton(eng_form)
        if not ar_skel or not eng_skel:
            return None
        try:
            variants = project_root_by_target(ar_variant, "european")
        except Exception:
            variants = project_root_sound_laws(ar_variant, include_group_expansion=True, max_variants=128)
        score, best_var = _weighted_projection_score(ar_skel, eng_skel, variants)
        if score <= 0.0:
            return None
        return MethodResult(
            method_name="position_weighted",
            score=score,
            explanation=f"Position-weighted match (H8): '{best_var}' ↔ '{eng_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_ipa_scoring(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        ipa_lookup = self._get_ipa_lookup()
        ipa_skel = ipa_lookup.ipa_consonant_skeleton(eng_form)
        if not ipa_skel:
            return None
        score, best_var = _best_projection_match_ipa(ar_variant, ipa_skel)
        if score <= 0.0:
            return None
        return MethodResult(
            method_name="ipa_scoring",
            score=score,
            explanation=f"IPA skeleton '{ipa_skel}' matched projection '{best_var}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_reverse_root(
        self, ar_variant: str, eng_form: str
    ) -> MethodResult | None:
        """Generate possible Arabic roots from English consonants and check overlap."""
        eng_skel = _english_consonant_skeleton(eng_form)
        if not eng_skel:
            return None
        candidates = self._reverse_generate_arabic(eng_skel)
        if not candidates:
            return None
        ar_skel = _arabic_consonant_skeleton(ar_variant)
        if not ar_skel:
            return None
        best_score, best_cand = 0.0, ""
        for cand in candidates:
            score = SequenceMatcher(None, cand, ar_skel).ratio()
            if score > best_score:
                best_score, best_cand = score, cand
        if best_score <= 0.0:
            return None
        return MethodResult(
            method_name="reverse_root",
            score=best_score,
            explanation=f"Reverse-generated '{best_cand}' from '{eng_skel}', matched Arabic '{ar_skel}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_synonym_expansion(
        self, ar_variant: str, original_root: str, eng_form: str
    ) -> MethodResult | None:
        """Score a synonym variant of the original Arabic root."""
        if ar_variant == original_root:
            return None  # original handled by direct_skeleton
        score = self._score_skeleton_pair(ar_variant, eng_form)
        if score <= 0.0:
            return None
        return MethodResult(
            method_name="synonym_expansion",
            score=score,
            explanation=f"Synonym '{ar_variant}' of root '{original_root}' matched '{eng_form}'",
            arabic_variant_used=ar_variant,
            english_variant_used=eng_form,
        )

    def _method_article_detection(
        self, ar_variant: str, eng_form: str
    ) -> list[MethodResult]:
        results: list[MethodResult] = []
        stripped_forms = self._strip_article(eng_form)
        for stripped in stripped_forms:
            if stripped == eng_form.lower():
                continue
            score = self._score_skeleton_pair(ar_variant, stripped)
            if score <= 0.0:
                continue
            results.append(MethodResult(
                method_name="article_detection",
                score=score,
                explanation=(
                    f"Arabic article absorbed: '{eng_form}' stripped to '{stripped}', "
                    f"matched Arabic '{ar_variant}'"
                ),
                arabic_variant_used=ar_variant,
                english_variant_used=stripped,
            ))
        return results

    # ------------------------------------------------------------------
    # Run all methods for one (ar_variant, eng_form) pair
    # ------------------------------------------------------------------

    def _run_all_methods(
        self,
        ar_variant: str,
        eng_form: str,
        original_arabic: str,
        is_dialect: bool = False,
        dialect_name: str = "",
    ) -> list[MethodResult]:
        results: list[MethodResult] = []

        direct = self._method_direct_skeleton(ar_variant, eng_form)
        if direct:
            results.append(direct)

        results.extend(self._method_morpheme_decomposition(ar_variant, eng_form))

        multi_hop = self._method_multi_hop(ar_variant, eng_form)
        if multi_hop:
            results.append(multi_hop)

        guttural = self._method_guttural_projection(ar_variant, eng_form)
        if guttural:
            results.append(guttural)

        emphatic = self._method_emphatic_collapse(ar_variant, eng_form)
        if emphatic:
            results.append(emphatic)

        meta = self._method_metathesis(ar_variant, eng_form)
        if meta:
            results.append(meta)

        if is_dialect and dialect_name:
            dialect_r = self._method_dialect_variant(ar_variant, eng_form, dialect_name)
            if dialect_r:
                results.append(dialect_r)

        pos = self._method_position_weighted(ar_variant, eng_form)
        if pos:
            results.append(pos)

        ipa = self._method_ipa_scoring(ar_variant, eng_form)
        if ipa:
            results.append(ipa)

        rev = self._method_reverse_root(ar_variant, eng_form)
        if rev:
            results.append(rev)

        syn = self._method_synonym_expansion(ar_variant, original_arabic, eng_form)
        if syn:
            results.append(syn)

        results.extend(self._method_article_detection(ar_variant, eng_form))

        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_pair(self, source: dict[str, Any], target: dict[str, Any]) -> MultiMethodScore:
        """Run all methods on a single pair, return combined result."""
        arabic_root = str(
            source.get("root_norm")
            or source.get("root")
            or source.get("translit")
            or source.get("lemma")
            or ""
        ).strip()
        english_word = str(
            target.get("lemma")
            or target.get("translit")
            or ""
        ).strip()

        if not arabic_root or not english_word:
            return MultiMethodScore(
                best_score=0.0,
                best_method="",
                all_results=[],
                arabic_expansions_tried=0,
                methods_that_fired=[],
            )

        all_results: list[MethodResult] = []

        # 1. Get all Arabic variants (synonyms + dialect)
        arabic_variants = self._expand_arabic(arabic_root)

        # 2. Get English decompositions (stems to try)
        eng_decompositions = self._decompose_english(english_word)
        eng_forms = list({stem for _, stem, _ in eng_decompositions if stem})
        # Also include article-stripped forms as top-level English forms
        for stripped in self._strip_article(english_word):
            if stripped not in eng_forms:
                eng_forms.append(stripped)

        # Determine which variants are dialect-derived
        normalized_root = normalize_arabic_root(arabic_root)
        dialect_variants: dict[str, str] = {}  # variant -> dialect_name
        for dialect, shifts in _DIALECT_SHIFTS.items():
            dv = normalized_root
            for ar_letter, replacement in shifts.items():
                dv = dv.replace(ar_letter, replacement)
            if dv != normalized_root:
                dialect_variants[dv] = dialect

        # 3. Run each method for each (ar_variant, eng_form) combination
        for ar_variant in arabic_variants:
            is_dialect = ar_variant in dialect_variants
            dialect_name = dialect_variants.get(ar_variant, "")
            for eng_form in eng_forms:
                batch = self._run_all_methods(
                    ar_variant,
                    eng_form,
                    original_arabic=arabic_root,
                    is_dialect=is_dialect,
                    dialect_name=dialect_name,
                )
                all_results.extend(batch)

        if not all_results:
            return MultiMethodScore(
                best_score=0.0,
                best_method="",
                all_results=[],
                arabic_expansions_tried=len(arabic_variants),
                methods_that_fired=[],
            )

        # 4. Pick best result
        best = max(all_results, key=lambda r: r.score)
        methods_fired = list({r.method_name for r in all_results if r.score > 0.4})

        return MultiMethodScore(
            best_score=round(best.score, 6),
            best_method=best.method_name,
            all_results=all_results,
            arabic_expansions_tried=len(arabic_variants),
            methods_that_fired=sorted(methods_fired),
        )
