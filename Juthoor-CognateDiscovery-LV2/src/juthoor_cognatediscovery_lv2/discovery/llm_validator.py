"""LLM-based etymology validation using Claude API.

Sends candidate Arabic-English pairs to Claude for etymological reasoning.
The LLM evaluates whether the pair could be genuinely related using all
14 linking methods from our methodology.

Usage:
    validator = LLMEtymologyValidator()
    result = validator.validate_pair(
        arabic_root="رثى",
        arabic_meaning="to feel pity, compassion",
        english_word="ruth",
        english_meaning="pity, mercy",
        phonetic_score=0.85,
    )
    # result.confidence = 0.9
    # result.reasoning = "Direct phonetic match: r-th-a -> r-th. Semantic match: both mean compassion..."
    # result.method_used = "direct_skeleton"
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMValidationResult:
    confidence: float
    reasoning: str
    method_used: str
    is_cognate: bool
    phonetic_rules_identified: list[str]
    semantic_link: str
    intermediate_languages: list[str]
    raw_response: str


class LLMEtymologyValidator:
    """Validates etymology candidates using Claude API."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001", max_concurrent: int = 5):
        self._model = model
        self._client = None
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def available(self) -> bool:
        """Check if Claude API is available."""
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def validate_pair(
        self,
        arabic_root: str,
        arabic_meaning: str,
        english_word: str,
        english_meaning: str,
        phonetic_score: float = 0.0,
        additional_context: str = "",
    ) -> LLMValidationResult:
        """Validate a single candidate pair."""
        if not self.available:
            return LLMValidationResult(
                confidence=phonetic_score,
                reasoning="LLM validation unavailable (no API key)",
                method_used="phonetic_only",
                is_cognate=phonetic_score > 0.6,
                phonetic_rules_identified=[],
                semantic_link="",
                intermediate_languages=[],
                raw_response="",
            )

        prompt = self._build_prompt(
            arabic_root, arabic_meaning,
            english_word, english_meaning,
            phonetic_score, additional_context,
        )

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self._model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            return self._parse_response(raw, phonetic_score)
        except Exception as e:
            return LLMValidationResult(
                confidence=phonetic_score * 0.8,
                reasoning=f"LLM call failed: {e}",
                method_used="phonetic_fallback",
                is_cognate=phonetic_score > 0.6,
                phonetic_rules_identified=[],
                semantic_link="",
                intermediate_languages=[],
                raw_response=str(e),
            )

    def validate_batch(
        self,
        pairs: list[dict[str, Any]],
    ) -> list[LLMValidationResult]:
        """Validate a batch of pairs.

        Each dict must contain: arabic_root, arabic_meaning, english_word,
        english_meaning, phonetic_score. Optional: additional_context.
        """
        _allowed = {
            "arabic_root", "arabic_meaning", "english_word", "english_meaning",
            "phonetic_score", "additional_context",
        }
        return [
            self.validate_pair(**{k: v for k, v in pair.items() if k in _allowed})
            for pair in pairs
        ]

    def _build_prompt(
        self,
        arabic_root: str,
        arabic_meaning: str,
        english_word: str,
        english_meaning: str,
        phonetic_score: float,
        additional_context: str,
    ) -> str:
        context_line = f"Additional context: {additional_context}" if additional_context else ""
        return f"""You are a comparative linguistics expert specializing in Arabic-European etymology.

Evaluate whether the Arabic root and English word could be etymologically related.

Arabic root: {arabic_root}
Arabic meaning: {arabic_meaning}
English word: {english_word}
English meaning: {english_meaning}
Phonetic similarity score: {phonetic_score:.2f}
{context_line}

Known sound correspondence rules (Arabic -> English):
- ق -> c/k/g (uvular -> velar)
- ع -> silent/h (pharyngeal deletion)
- ح -> h (pharyngeal -> glottal)
- خ -> h/k/ch (velar fricative)
- غ -> g (voiced uvular -> velar)
- ص -> s (emphatic -> plain)
- ط -> t (emphatic -> plain)
- ض -> d (emphatic -> plain)
- ث -> th/t/s
- ذ -> th/d/z
- ف -> f/p (labial interchange)
- ب -> b/p/v (labial interchange)

Respond in this EXACT JSON format (no markdown, just JSON):
{{
  "confidence": 0.0-1.0,
  "is_cognate": true/false,
  "reasoning": "2-3 sentence explanation",
  "method": "direct_match|morpheme_decomposition|semantic_drift|multi_hop_chain|metathesis|dialect_variant|article_absorption|other",
  "phonetic_rules": ["rule1", "rule2"],
  "semantic_link": "how meanings connect",
  "intermediate_languages": ["Latin", "Greek"]
}}"""

    def _parse_response(self, raw: str, fallback_score: float) -> LLMValidationResult:
        """Parse LLM JSON response, handling optional markdown code fences."""
        try:
            text = raw.strip()
            if text.startswith("```"):
                # Strip opening fence (```json or ```)
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:]
                # Strip closing fence if present
                if text.endswith("```"):
                    text = text[:-3]
            data = json.loads(text.strip())
            return LLMValidationResult(
                confidence=float(data.get("confidence", fallback_score)),
                reasoning=str(data.get("reasoning", "")),
                method_used=str(data.get("method", "unknown")),
                is_cognate=bool(data.get("is_cognate", False)),
                phonetic_rules_identified=list(data.get("phonetic_rules", [])),
                semantic_link=str(data.get("semantic_link", "")),
                intermediate_languages=list(data.get("intermediate_languages", [])),
                raw_response=raw,
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return LLMValidationResult(
                confidence=fallback_score * 0.8,
                reasoning=raw[:200],
                method_used="parse_failed",
                is_cognate=fallback_score > 0.6,
                phonetic_rules_identified=[],
                semantic_link="",
                intermediate_languages=[],
                raw_response=raw,
            )
