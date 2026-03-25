from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from juthoor_arabicgenome_lv1.core.feature_decomposition import FEATURE_TO_CATEGORY
from juthoor_arabicgenome_lv1.factory.scoring import (
    SYNONYM_GROUPS,
    blended_jaccard,
    category_jaccard,
    jaccard_similarity,
)


_FEATURE_TO_CANONICAL: dict[str, str] = {}
for _group in SYNONYM_GROUPS:
    _canon = min(_group)
    for _feature in _group:
        _FEATURE_TO_CANONICAL[_feature] = _canon

FEATURE_GLOSSES_EN: dict[str, str] = {
    "تجمع": "gathering",
    "تلاصق": "adhesion",
    "امتداد": "extension",
    "استرسال": "continuous flow",
    "نفاذ": "penetration",
    "خروج": "emergence",
    "باطن": "inner depth",
    "فراغ": "void",
    "احتباس": "retention",
    "قوة": "force",
    "غلظ": "thickness",
    "دقة": "fineness",
    "انتشار": "spreading",
    "اكتناز": "compaction",
    "حدة": "sharpness",
    "اشتمال": "encompassing",
    "احتكاك": "friction",
    "جفاف": "dryness",
    "ضغط": "pressure",
    "إمساك": "holding",
    "استقلال": "separation",
    "ظاهر": "manifest surface",
    "رخاوة": "soft looseness",
    "اتساع": "expansion",
    "رجوع": "return",
    "استقرار": "stability",
    "عمق": "depth",
    "خلوص": "release",
    "قطع": "cutting",
    "صعود": "rising",
    "نقص": "diminution",
    "رقة": "delicacy",
    "تعقد": "complexity",
    "تماسك": "cohesion",
}

SCHOLAR_ORDER = ("jabal", "asim_al_masri", "hassan_abbas", "neili", "anbar")


@dataclass(frozen=True)
class PositionSummary:
    total_nuclei: int
    total_member_weight: int
    feature_weights: dict[str, int]
    category_weights: dict[str, int]
    top_features: list[dict[str, Any]]
    top_categories: list[dict[str, Any]]


def _canonicalize_features(features: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for feature in features:
        canonical = _FEATURE_TO_CANONICAL.get(feature, feature)
        if canonical not in seen:
            ordered.append(canonical)
            seen.add(canonical)
    return tuple(ordered)


def _weighted_feature_counts(rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int], int]:
    feature_weights: dict[str, int] = defaultdict(int)
    category_weights: dict[str, int] = defaultdict(int)
    total_weight = 0
    for row in rows:
        member_count = int(row.get("member_count") or 0)
        total_weight += member_count
        features = _canonicalize_features(row.get("features") or [])
        categories = {FEATURE_TO_CATEGORY.get(feature, "unknown") for feature in features}
        for feature in features:
            feature_weights[feature] += member_count
        for category in categories:
            if category != "unknown":
                category_weights[category] += member_count
    return dict(feature_weights), dict(category_weights), total_weight


def _sorted_weight_rows(weights: dict[str, int], total_weight: int) -> list[dict[str, Any]]:
    if total_weight <= 0:
        return []
    ordered = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    return [
        {
            "item": item,
            "weight": weight,
            "rate": round(weight / total_weight, 6),
        }
        for item, weight in ordered
    ]


def summarize_position(rows: list[dict[str, Any]]) -> PositionSummary:
    feature_weights, category_weights, total_weight = _weighted_feature_counts(rows)
    return PositionSummary(
        total_nuclei=len(rows),
        total_member_weight=total_weight,
        feature_weights=feature_weights,
        category_weights=category_weights,
        top_features=_sorted_weight_rows(feature_weights, total_weight),
        top_categories=_sorted_weight_rows(category_weights, total_weight),
    )


def _shared_feature_candidates(l1: PositionSummary, l2: PositionSummary) -> list[dict[str, Any]]:
    shared = set(l1.feature_weights) & set(l2.feature_weights)
    candidates: list[dict[str, Any]] = []
    for feature in shared:
        left = l1.feature_weights[feature]
        right = l2.feature_weights[feature]
        left_rate = left / l1.total_member_weight if l1.total_member_weight else 0.0
        right_rate = right / l2.total_member_weight if l2.total_member_weight else 0.0
        candidates.append(
            {
                "feature": feature,
                "left_weight": left,
                "right_weight": right,
                "left_rate": round(left_rate, 6),
                "right_rate": round(right_rate, 6),
                "intersection_score": round(min(left_rate, right_rate), 6),
                "combined_weight": left + right,
                "category": FEATURE_TO_CATEGORY.get(feature, "unknown"),
            }
        )
    return sorted(
        candidates,
        key=lambda row: (-row["intersection_score"], -row["combined_weight"], row["feature"]),
    )


def _shared_category_candidates(l1: PositionSummary, l2: PositionSummary) -> list[dict[str, Any]]:
    shared = set(l1.category_weights) & set(l2.category_weights)
    candidates: list[dict[str, Any]] = []
    for category in shared:
        left = l1.category_weights[category]
        right = l2.category_weights[category]
        left_rate = left / l1.total_member_weight if l1.total_member_weight else 0.0
        right_rate = right / l2.total_member_weight if l2.total_member_weight else 0.0
        candidates.append(
            {
                "category": category,
                "left_weight": left,
                "right_weight": right,
                "left_rate": round(left_rate, 6),
                "right_rate": round(right_rate, 6),
                "intersection_score": round(min(left_rate, right_rate), 6),
                "combined_weight": left + right,
            }
        )
    return sorted(
        candidates,
        key=lambda row: (-row["intersection_score"], -row["combined_weight"], row["category"]),
    )


def _representative_feature_for_category(
    category: str,
    l1: PositionSummary,
    l2: PositionSummary,
) -> str | None:
    candidates: list[tuple[int, str]] = []
    for feature, weight in l1.feature_weights.items():
        if FEATURE_TO_CATEGORY.get(feature) == category:
            candidates.append((weight + l2.feature_weights.get(feature, 0), feature))
    for feature, weight in l2.feature_weights.items():
        if FEATURE_TO_CATEGORY.get(feature) == category and feature not in {item[1] for item in candidates}:
            candidates.append((weight + l1.feature_weights.get(feature, 0), feature))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def derive_letter_meaning(entry: dict[str, Any]) -> dict[str, Any]:
    l1_rows = list(entry.get("as_letter1") or [])
    l2_rows = list(entry.get("as_letter2") or [])
    l1 = summarize_position(l1_rows)
    l2 = summarize_position(l2_rows)
    shared_features = _shared_feature_candidates(l1, l2)
    shared_categories = _shared_category_candidates(l1, l2)

    selected_features: list[str] = []
    structure = "unified"
    confidence = "medium"

    if entry.get("total", 0) < 8 or min(l1.total_nuclei, l2.total_nuclei) < 2:
        structure = "sparse"
        confidence = "low"
    if shared_features:
        top_score = shared_features[0]["intersection_score"]
        threshold = max(0.08, top_score * 0.55)
        selected_features = [
            row["feature"]
            for row in shared_features
            if row["intersection_score"] >= threshold
        ][:3]
    elif shared_categories:
        top_score = shared_categories[0]["intersection_score"]
        threshold = max(0.08, top_score * 0.55)
        for row in shared_categories:
            if row["intersection_score"] < threshold:
                continue
            representative = _representative_feature_for_category(row["category"], l1, l2)
            if representative and representative not in selected_features:
                selected_features.append(representative)
        selected_features = selected_features[:2]
        structure = "dual_aspect" if len(selected_features) > 1 else structure
    else:
        fallback_candidates = [feature["item"] for feature in l1.top_features[:1] + l2.top_features[:1]]
        selected_features = list(dict.fromkeys(fallback_candidates))[:2]
        structure = "dual_aspect" if len(selected_features) > 1 else "sparse"
        confidence = "low"

    if confidence != "low":
        if entry.get("total", 0) >= 24 and shared_features and shared_features[0]["intersection_score"] >= 0.18:
            confidence = "high"
        elif entry.get("total", 0) >= 14 and (shared_features or shared_categories):
            confidence = "medium_high"
        else:
            confidence = "medium"

    if (
        len(selected_features) > 1
        and len({FEATURE_TO_CATEGORY.get(feature, "unknown") for feature in selected_features}) > 1
        and structure != "sparse"
    ):
        structure = "dual_aspect"

    meaning_ar = " + ".join(selected_features) if selected_features else "غير محسوم"
    meaning_en = " + ".join(FEATURE_GLOSSES_EN.get(feature, feature) for feature in selected_features) if selected_features else "unresolved"

    return {
        "letter": entry["letter"],
        "count_l1": entry.get("count_l1", len(l1_rows)),
        "count_l2": entry.get("count_l2", len(l2_rows)),
        "total_nuclei": entry.get("total", len(l1_rows) + len(l2_rows)),
        "position_summaries": {
            "as_letter1": {
                "total_nuclei": l1.total_nuclei,
                "total_member_weight": l1.total_member_weight,
                "top_features": l1.top_features[:8],
                "top_categories": l1.top_categories[:5],
            },
            "as_letter2": {
                "total_nuclei": l2.total_nuclei,
                "total_member_weight": l2.total_member_weight,
                "top_features": l2.top_features[:8],
                "top_categories": l2.top_categories[:5],
            },
        },
        "shared_features": shared_features[:8],
        "shared_categories": shared_categories[:5],
        "selected_features": selected_features,
        "empirical_meaning_ar": meaning_ar,
        "empirical_gloss_en": meaning_en,
        "structure": structure,
        "confidence": confidence,
        "evidence_as_letter1": l1_rows,
        "evidence_as_letter2": l2_rows,
    }


def compare_scholars(
    derived_rows: list[dict[str, Any]],
    scholar_letter_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scholar_map: dict[str, dict[str, tuple[str, ...]]] = defaultdict(dict)
    for row in scholar_letter_rows:
        scholar = row.get("scholar")
        letter = row.get("letter")
        if not scholar or not letter:
            continue
        scholar_map[scholar][letter] = tuple(row.get("atomic_features") or ())

    out: list[dict[str, Any]] = []
    for row in derived_rows:
        derived = tuple(row.get("selected_features") or ())
        comparisons: dict[str, Any] = {}
        for scholar in SCHOLAR_ORDER:
            scholar_features = scholar_map.get(scholar, {}).get(row["letter"])
            if scholar_features is None:
                comparisons[scholar] = {
                    "classification": "no_data",
                    "features": [],
                    "jaccard": None,
                    "category_jaccard": None,
                    "blended_jaccard": None,
                }
                continue
            feat_j = jaccard_similarity(derived, scholar_features)
            cat_j = category_jaccard(derived, scholar_features)
            blend = blended_jaccard(derived, scholar_features)
            if blend >= 0.67 or feat_j >= 0.5:
                classification = "match"
            elif blend >= 0.2 or cat_j > 0.0:
                classification = "partial"
            else:
                classification = "conflict"
            comparisons[scholar] = {
                "classification": classification,
                "features": list(_canonicalize_features(scholar_features)),
                "jaccard": round(feat_j, 6),
                "category_jaccard": round(cat_j, 6),
                "blended_jaccard": round(blend, 6),
            }
        enriched = dict(row)
        enriched["scholar_comparison"] = comparisons
        out.append(enriched)
    return out


def derive_independent_letter_meanings(
    full_letter_nucleus_evidence: dict[str, dict[str, Any]],
    scholar_letter_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    derived = [
        derive_letter_meaning(full_letter_nucleus_evidence[letter])
        for letter in full_letter_nucleus_evidence
    ]
    return compare_scholars(derived, scholar_letter_rows)


def render_independent_letter_genome_markdown(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "# الجينوم الحرفي العربي المستقل",
        "## Independent Blind-First Derivation of Arabic Letter Meanings",
        "",
        "**Method:** weighted bottom-up derivation from `full_letter_nucleus_evidence.json`",
        "**Blindness rule:** scholar files were used only after the empirical meaning was derived",
        "",
        "This report derives a semantic meaning for each Arabic letter from binary nucleus evidence alone.",
        "Each meaning is based on the stable cross-position thread that survives both `as_letter1` and `as_letter2` evidence.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['letter']} — {row['confidence']} / {row['structure']}",
                "",
                f"**Empirical meaning:** {row['empirical_meaning_ar']}",
                f"**English gloss:** {row['empirical_gloss_en']}",
                f"**Coverage:** {row['total_nuclei']} nuclei (`L1={row['count_l1']}`, `L2={row['count_l2']}`)",
                "",
                "**Dominant weighted features as L1:**",
            ]
        )
        for item in row["position_summaries"]["as_letter1"]["top_features"][:5]:
            lines.append(f"- {item['item']} — weight {item['weight']} ({item['rate']:.1%})")
        lines.append("")
        lines.append("**Dominant weighted features as L2:**")
        for item in row["position_summaries"]["as_letter2"]["top_features"][:5]:
            lines.append(f"- {item['item']} — weight {item['weight']} ({item['rate']:.1%})")
        lines.append("")
        lines.append("**Shared evidence thread:**")
        if row["shared_features"]:
            for item in row["shared_features"][:5]:
                lines.append(
                    f"- {item['feature']} — L1 {item['left_rate']:.1%}, L2 {item['right_rate']:.1%}, score {item['intersection_score']:.1%}"
                )
        elif row["shared_categories"]:
            for item in row["shared_categories"][:3]:
                lines.append(
                    f"- category `{item['category']}` — L1 {item['left_rate']:.1%}, L2 {item['right_rate']:.1%}"
                )
        else:
            lines.append("- no exact shared thread; meaning chosen from the strongest surviving weighted evidence")
        lines.append("")
        lines.append("**Scholar comparison (post-derivation):**")
        for scholar in SCHOLAR_ORDER:
            comparison = row["scholar_comparison"][scholar]
            if comparison["classification"] == "no_data":
                lines.append(f"- {scholar}: no_data")
            else:
                lines.append(
                    f"- {scholar}: {comparison['classification']} — {', '.join(comparison['features']) or '∅'} "
                    f"(blend={comparison['blended_jaccard']:.3f})"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_full_letter_nucleus_evidence(path: Path) -> dict[str, dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))
