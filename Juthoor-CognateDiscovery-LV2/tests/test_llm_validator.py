"""Tests for LLMEtymologyValidator."""

import os

import pytest

from juthoor_cognatediscovery_lv2.discovery.llm_validator import (
    LLMEtymologyValidator,
    LLMValidationResult,
)


def test_validator_no_api_key():
    """When no API key, should return fallback result."""
    old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        v = LLMEtymologyValidator()
        assert not v.available
        result = v.validate_pair("رثى", "pity", "ruth", "pity", 0.8)
        assert result.confidence == 0.8
        assert "unavailable" in result.reasoning
        assert result.method_used == "phonetic_only"
    finally:
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key


def test_validator_available_with_key(monkeypatch):
    """When API key is set, available should be True."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
    v = LLMEtymologyValidator()
    assert v.available


def test_build_prompt():
    v = LLMEtymologyValidator()
    prompt = v._build_prompt("رثى", "pity", "ruth", "mercy", 0.85, "")
    assert "رثى" in prompt
    assert "ruth" in prompt
    assert "ق -> c/k/g" in prompt
    assert "0.85" in prompt
    # No spurious context line when additional_context is empty
    assert "Additional context:" not in prompt


def test_build_prompt_with_context():
    v = LLMEtymologyValidator()
    prompt = v._build_prompt("رثى", "pity", "ruth", "mercy", 0.5, "via Old English")
    assert "Additional context: via Old English" in prompt


def test_parse_response_valid_json():
    v = LLMEtymologyValidator()
    raw = (
        '{"confidence": 0.9, "is_cognate": true, "reasoning": "test", '
        '"method": "direct_match", "phonetic_rules": ["th<->ث"], '
        '"semantic_link": "both mean pity", "intermediate_languages": []}'
    )
    result = v._parse_response(raw, 0.5)
    assert result.confidence == 0.9
    assert result.is_cognate is True
    assert result.method_used == "direct_match"
    assert result.phonetic_rules_identified == ["th<->ث"]
    assert result.semantic_link == "both mean pity"
    assert result.intermediate_languages == []
    assert result.raw_response == raw


def test_parse_response_markdown_wrapped():
    v = LLMEtymologyValidator()
    raw = (
        "```json\n"
        '{"confidence": 0.8, "is_cognate": true, "reasoning": "test", '
        '"method": "direct_match", "phonetic_rules": [], '
        '"semantic_link": "", "intermediate_languages": []}\n'
        "```"
    )
    result = v._parse_response(raw, 0.5)
    assert result.confidence == 0.8
    assert result.is_cognate is True


def test_parse_response_plain_fenced():
    """Handles ``` without json label."""
    v = LLMEtymologyValidator()
    raw = (
        "```\n"
        '{"confidence": 0.7, "is_cognate": false, "reasoning": "no link", '
        '"method": "other", "phonetic_rules": [], '
        '"semantic_link": "none", "intermediate_languages": []}\n'
        "```"
    )
    result = v._parse_response(raw, 0.5)
    assert result.confidence == 0.7
    assert result.is_cognate is False


def test_parse_response_invalid():
    v = LLMEtymologyValidator()
    result = v._parse_response("not json at all", 0.5)
    assert result.confidence == pytest.approx(0.4)  # fallback * 0.8
    assert result.method_used == "parse_failed"
    assert result.is_cognate is False  # 0.5 not > 0.6


def test_parse_response_invalid_high_score():
    """With fallback_score > 0.6 and bad JSON, is_cognate should be True."""
    v = LLMEtymologyValidator()
    result = v._parse_response("bad json", 0.9)
    assert result.is_cognate is True
    assert result.confidence == pytest.approx(0.72)  # 0.9 * 0.8


def test_parse_response_missing_fields():
    """Partial JSON should use defaults without crashing."""
    v = LLMEtymologyValidator()
    raw = '{"confidence": 0.6}'
    result = v._parse_response(raw, 0.5)
    assert result.confidence == 0.6
    assert result.method_used == "unknown"
    assert result.phonetic_rules_identified == []
    assert result.intermediate_languages == []


def test_batch_validation_no_key():
    """Batch returns one result per pair even without API key."""
    old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        v = LLMEtymologyValidator()
        pairs = [
            {
                "arabic_root": "رثى",
                "arabic_meaning": "pity",
                "english_word": "ruth",
                "english_meaning": "pity",
                "phonetic_score": 0.8,
            },
            {
                "arabic_root": "لفت",
                "arabic_meaning": "turn",
                "english_word": "left",
                "english_meaning": "opposite of right",
                "phonetic_score": 0.9,
            },
        ]
        results = v.validate_batch(pairs)
        assert len(results) == 2
        assert all(isinstance(r, LLMValidationResult) for r in results)
        assert results[0].confidence == 0.8
        assert results[1].confidence == 0.9
    finally:
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key


def test_batch_ignores_extra_keys():
    """Extra keys in batch dicts are silently ignored."""
    old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        v = LLMEtymologyValidator()
        pairs = [
            {
                "arabic_root": "رثى",
                "arabic_meaning": "pity",
                "english_word": "ruth",
                "english_meaning": "pity",
                "phonetic_score": 0.7,
                "extra_field": "should be ignored",
                "rank": 1,
            }
        ]
        results = v.validate_batch(pairs)
        assert len(results) == 1
        assert results[0].confidence == 0.7
    finally:
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key


def test_fallback_is_cognate_boundary():
    """is_cognate threshold: > 0.6, so 0.6 exactly is False."""
    old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        v = LLMEtymologyValidator()
        result_low = v.validate_pair("abc", "x", "def", "y", phonetic_score=0.6)
        result_high = v.validate_pair("abc", "x", "def", "y", phonetic_score=0.61)
        assert result_low.is_cognate is False
        assert result_high.is_cognate is True
    finally:
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key


def test_client_lazy_init():
    """Client is not initialized until first API call."""
    old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        v = LLMEtymologyValidator()
        assert v._client is None
    finally:
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key
