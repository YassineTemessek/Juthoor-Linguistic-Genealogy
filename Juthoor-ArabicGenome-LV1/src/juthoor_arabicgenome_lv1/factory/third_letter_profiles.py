"""Third-letter modifier profiling for LV1 prediction analysis.

This module aggregates per-letter modifier behavior, stability, and blockage
signals across scholars to build summary profiles for third letters.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


def _rate(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return count / total


def _top_fractional_features(counter: Counter[str], total: int, *, threshold: float = 0.6) -> list[str]:
    if total <= 0:
        return []
    return [
        feature
        for feature, count in counter.most_common()
        if _rate(count, total) >= threshold
    ]


def _modifier_band(*, mean_blended: float, nonzero_rate: float, blocked_rate: float) -> str:
    if mean_blended >= 0.24 and nonzero_rate >= 0.68 and blocked_rate <= 0.05:
        return "supportive"
    if mean_blended < 0.17 or blocked_rate >= 0.2:
        return "risky"
    return "mixed"


def build_third_letter_modifier_profiles(
    rows: list[dict[str, Any]],
    *,
    scholars: tuple[str, ...] = ("consensus_weighted", "consensus_strict"),
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    for scholar in scholars:
        scholar_rows = [row for row in rows if row.get("scholar") == scholar]
        by_letter: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in scholar_rows:
            by_letter[str(row.get("third_letter") or "")].append(row)

        for letter, letter_rows in by_letter.items():
            filtered_counter: Counter[str] = Counter()
            dropped_counter: Counter[str] = Counter()
            model_counter: Counter[str] = Counter()
            quranic_rows = 0
            nonzero = 0
            dropped_rows = 0
            predicted_feature_total = 0
            matched_feature_total = 0

            for row in letter_rows:
                model_counter.update([str(row.get("model") or "")])
                filtered_counter.update(str(feature) for feature in row.get("filtered_third_letter_features", []))
                dropped = [str(feature) for feature in row.get("dropped_third_letter_features", [])]
                dropped_counter.update(dropped)
                if dropped:
                    dropped_rows += 1
                if row.get("quranic_verse"):
                    quranic_rows += 1
                if float(row.get("blended_jaccard", 0.0)) > 0.0:
                    nonzero += 1
                predicted = set(str(feature) for feature in row.get("predicted_features", []))
                actual = set(str(feature) for feature in row.get("actual_features", []))
                predicted_feature_total += len(predicted)
                matched_feature_total += len(predicted & actual)

            total_rows = len(letter_rows)
            grouped[letter][scholar] = {
                "rows": total_rows,
                "quranic_rows": quranic_rows,
                "mean_blended_jaccard": round(mean(float(row.get("blended_jaccard", 0.0)) for row in letter_rows), 6),
                "nonzero_rate": round(_rate(nonzero, total_rows), 6),
                "quranic_rate": round(_rate(quranic_rows, total_rows), 6),
                "feature_precision": round(_rate(matched_feature_total, predicted_feature_total), 6),
                "dropped_feature_row_rate": round(_rate(dropped_rows, total_rows), 6),
                "dominant_models": [
                    {"model": model, "count": count}
                    for model, count in model_counter.most_common(3)
                    if model
                ],
                "stable_modifier_features": _top_fractional_features(filtered_counter, total_rows),
                "blocked_modifier_features": _top_fractional_features(dropped_counter, total_rows, threshold=0.05),
                "top_modifier_features": [
                    {"feature": feature, "count": count}
                    for feature, count in filtered_counter.most_common(5)
                ],
                "top_blocked_features": [
                    {"feature": feature, "count": count}
                    for feature, count in dropped_counter.most_common(5)
                ],
            }

    profiles: list[dict[str, Any]] = []
    for letter, scholar_map in sorted(grouped.items()):
        if not scholar_map:
            continue
        shared_stable = set.intersection(
            *(set(data["stable_modifier_features"]) for data in scholar_map.values())
        ) if scholar_map else set()
        shared_blocked = set.intersection(
            *(set(data["blocked_modifier_features"]) for data in scholar_map.values())
        ) if scholar_map else set()
        mean_blended = mean(data["mean_blended_jaccard"] for data in scholar_map.values())
        nonzero_rate = mean(data["nonzero_rate"] for data in scholar_map.values())
        blocked_rate = mean(data["dropped_feature_row_rate"] for data in scholar_map.values())
        profiles.append(
            {
                "letter": letter,
                "summary_band": _modifier_band(
                    mean_blended=mean_blended,
                    nonzero_rate=nonzero_rate,
                    blocked_rate=blocked_rate,
                ),
                "shared_stable_modifier_features": sorted(shared_stable),
                "shared_blocked_features": sorted(shared_blocked),
                "mean_blended_jaccard": round(mean_blended, 6),
                "nonzero_rate": round(nonzero_rate, 6),
                "dropped_feature_row_rate": round(blocked_rate, 6),
                "scholar_profiles": scholar_map,
            }
        )
    return profiles


def render_third_letter_modifier_profiles_markdown(
    profiles: list[dict[str, Any]],
    *,
    scholars: tuple[str, ...] = ("consensus_weighted", "consensus_strict"),
) -> str:
    lines: list[str] = [
        "# Third Letter Modifier Profiles",
        "",
        "**Scope:** consensus-based root predictions only (`consensus_weighted`, `consensus_strict`).",
        "",
        "**Method:** aggregate each letter in third position across all roots, using the kept third-letter features, dropped third-letter features, dominant routing model, blended score, and nonzero rate.",
        "",
        "## Headline",
        "",
        "- This report describes how each Arabic letter behaves specifically as a third-letter modifier, not as an intrinsic letter meaning.",
        "- `supportive` means the letter adds a stable modifier signature with good blended score and little blocked-feature pollution.",
        "- `mixed` means the letter contributes real signal but still depends heavily on routing or generic features.",
        "- `risky` means the letter often collapses into nucleus-only fallback or repeatedly triggers blocked/poison features.",
        "",
        "## Summary Table",
        "",
        "| Letter | Band | Mean blended | Nonzero rate | Dropped-feature row rate | Stable modifier signature | Shared blocked features |",
        "|---|---|---:|---:|---:|---|---|",
    ]

    for profile in sorted(profiles, key=lambda item: item["mean_blended_jaccard"], reverse=True):
        stable = ", ".join(profile["shared_stable_modifier_features"]) or "—"
        blocked = ", ".join(profile["shared_blocked_features"]) or "—"
        lines.append(
            f"| {profile['letter']} | {profile['summary_band']} | "
            f"{profile['mean_blended_jaccard']:.3f} | {profile['nonzero_rate']:.3f} | "
            f"{profile['dropped_feature_row_rate']:.3f} | {stable} | {blocked} |"
        )

    supportive = [p["letter"] for p in profiles if p["summary_band"] == "supportive"]
    risky = [p["letter"] for p in profiles if p["summary_band"] == "risky"]
    lines.extend(
        [
            "",
            "## High-Level Findings",
            "",
            f"- Strongest third-letter enrichers in the current matrix: {', '.join(supportive) or 'none'}",
            f"- Riskiest third-letter modifiers in the current matrix: {', '.join(risky) or 'none'}",
            "- The repeated poison pattern is still `التحام` as a third-letter-only feature, especially with `ر`, `ل`, `ب`, and `ع`.",
            "- Many letters route to `nucleus_only`, which means the nucleus still carries more of the signal than the modifier in a large share of roots.",
            "",
            "## Per-Letter Profiles",
        ]
    )

    for profile in sorted(profiles, key=lambda item: item["letter"]):
        lines.extend(
            [
                "",
                f"### {profile['letter']}",
                "",
                f"- Band: `{profile['summary_band']}`",
                f"- Mean blended score across consensus layers: `{profile['mean_blended_jaccard']:.3f}`",
                f"- Nonzero rate across consensus layers: `{profile['nonzero_rate']:.3f}`",
                f"- Dropped-feature row rate: `{profile['dropped_feature_row_rate']:.3f}`",
                f"- Stable modifier signature: {', '.join(profile['shared_stable_modifier_features']) or '—'}",
                f"- Shared blocked features: {', '.join(profile['shared_blocked_features']) or '—'}",
                "",
            ]
        )
        for scholar in scholars:
            scholar_profile = profile["scholar_profiles"].get(scholar)
            if not scholar_profile:
                continue
            top_models = ", ".join(
                f"{entry['model']} ({entry['count']})"
                for entry in scholar_profile["dominant_models"]
            ) or "—"
            top_features = ", ".join(
                f"{entry['feature']} ({entry['count']})"
                for entry in scholar_profile["top_modifier_features"][:4]
            ) or "—"
            top_blocked = ", ".join(
                f"{entry['feature']} ({entry['count']})"
                for entry in scholar_profile["top_blocked_features"][:3]
            ) or "—"
            lines.extend(
                [
                    f"- `{scholar}`: mean `{scholar_profile['mean_blended_jaccard']:.3f}`, nonzero `{scholar_profile['nonzero_rate']:.3f}`, quranic share `{scholar_profile['quranic_rate']:.3f}`, feature precision `{scholar_profile['feature_precision']:.3f}`",
                    f"- `{scholar}` dominant models: {top_models}",
                    f"- `{scholar}` top modifier features: {top_features}",
                    f"- `{scholar}` blocked features: {top_blocked}",
                ]
            )

    return "\n".join(lines) + "\n"
