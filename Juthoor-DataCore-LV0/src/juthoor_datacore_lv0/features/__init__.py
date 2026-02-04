"""
LV0 Features Module - Text field generation utilities.

This module provides deterministic text field builders for creating
form_text (for CANINE embeddings) and meaning_text (for SONAR embeddings).

Example:
    from juthoor_datacore_lv0.features import build_form_text, build_meaning_text

    form = build_form_text(language="ara", lemma="كتاب", translit="kitab")
    meaning, is_fallback = build_meaning_text(gloss_plain="book")
"""

from .build_text_fields import (
    TextFieldSpec,
    build_form_text,
    build_meaning_text,
    iter_text_fields,
)

__all__ = [
    "TextFieldSpec",
    "build_form_text",
    "build_meaning_text",
    "iter_text_fields",
]
