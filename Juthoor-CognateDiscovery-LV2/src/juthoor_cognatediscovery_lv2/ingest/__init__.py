"""
LV2 Ingest Module - Language corpus ingest stubs.

This module provides lightweight normalization helpers and ingest stubs
for various language corpora. The actual data ingestion happens in LV0;
this module provides language-specific preprocessing utilities.

Example:
    from juthoor_cognatediscovery_lv2.ingest import (
        derive_skeleton,
        normalize_record,
    )

Available utilities:
    - derive_skeleton: Extract consonant sequence from transliteration
    - derive_ort_trace: Get orthographic character trace
    - minimal_lexeme_defaults: Fill missing optional fields
    - normalize_record: Apply quick normalization to a record
"""

from .utils import (
    derive_skeleton,
    derive_ort_trace,
    minimal_lexeme_defaults,
    normalize_record,
)

__all__ = [
    "derive_skeleton",
    "derive_ort_trace",
    "minimal_lexeme_defaults",
    "normalize_record",
]
