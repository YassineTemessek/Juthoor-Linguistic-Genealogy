from __future__ import annotations

from typing import Any

from juthoor_arabicgenome_lv1.core.canon_models import QuranicSemanticProfile
from juthoor_arabicgenome_lv1.core.canon_pipeline import CanonRegistries, process_root


def build_quranic_profile(lemma: str, root: str, registries: CanonRegistries) -> QuranicSemanticProfile:
    existing = (registries.quranic_profiles or {}).get(lemma) if registries.quranic_profiles else None
    analysis = process_root(root, registries)

    return QuranicSemanticProfile(
        lemma=lemma,
        root=analysis.root,
        conceptual_meaning=(existing.conceptual_meaning if existing else None) or analysis.conceptual_meaning,
        binary_field_meaning=(existing.binary_field_meaning if existing else None) or analysis.binary_field_meaning,
        lexical_realization=(existing.lexical_realization if existing else None) or analysis.lexical_realization,
        letter_trace=(existing.letter_trace if existing else None) or analysis.letter_trace,
        contextual_constraints=(existing.contextual_constraints if existing else None)
        or tuple(f"missing:{layer}" for layer in analysis.missing_layers if layer != "letters"),
        contrast_lemmas=(existing.contrast_lemmas if existing else None) or tuple(),
        interpretive_notes=(existing.interpretive_notes if existing else None)
        or f"classification:{analysis.classification}",
        confidence=(existing.confidence if existing else "stub"),
        status=(existing.status if existing else "draft"),
    )


def build_interpretation_evidence_card(lemma: str, root: str, registries: CanonRegistries) -> dict[str, Any]:
    profile = build_quranic_profile(lemma, root, registries)
    return {
        "lemma": profile.lemma,
        "root": profile.root,
        "conceptual_meaning": profile.conceptual_meaning,
        "lexical_realization": profile.lexical_realization,
        "binary_field_meaning": profile.binary_field_meaning,
        "contextual_constraints": list(profile.contextual_constraints or ()),
        "contrast_lemmas": list(profile.contrast_lemmas or ()),
        "letter_trace": list(profile.letter_trace or ()),
        "interpretive_notes": profile.interpretive_notes,
        "confidence": profile.confidence,
        "status": profile.status,
    }
