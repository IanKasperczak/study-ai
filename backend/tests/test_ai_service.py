"""Unit tests for ai_service's pure helper functions.

No network calls here on purpose -- these are the deterministic pieces
(trimming, dedup, JSON extraction) that don't need a live provider.
"""
from app.services.ai_service import (
    _dedupe,
    _disable_thinking,
    _extract_json_object,
    _trim_to_sentence_boundary,
)


def test_trim_to_sentence_boundary_cuts_back_to_last_full_sentence():
    text = "Primera oracion completa. Segunda oracion cortada a la mit"
    assert _trim_to_sentence_boundary(text) == "Primera oracion completa."


def test_trim_to_sentence_boundary_leaves_complete_text_untouched():
    text = "Una respuesta que ya termino bien."
    assert _trim_to_sentence_boundary(text) == text


def test_trim_to_sentence_boundary_falls_back_to_word_boundary():
    # No sentence-ending punctuation anywhere: must not end mid-word.
    text = "palabra suelta sin puntos ni final cort"
    assert _trim_to_sentence_boundary(text) == "palabra suelta sin puntos ni final..."


def test_trim_to_sentence_boundary_keeps_raw_text_as_last_resort():
    # A single early period, and the last space is also too early to trim
    # to safely (one giant unbroken blob at the end) -- nothing safe to cut
    # back to, so the raw text is the least-bad option.
    text = "a b " + "sinespacios" * 20
    assert _trim_to_sentence_boundary(text) == text.rstrip()


def test_dedupe_preserves_order_and_drops_repeats_and_empties():
    assert _dedupe(["a", "", "b", "a", "c"]) == ["a", "b", "c"]


def test_extract_json_object_parses_embedded_json():
    content = 'Aca esta: {"invalid_indices": [1, 2]} listo.'
    assert _extract_json_object(content) == {"invalid_indices": [1, 2]}


def test_extract_json_object_returns_none_for_garbage():
    assert _extract_json_object("no json here") is None
    assert _extract_json_object("") is None


def test_disable_thinking_only_applies_to_nim():
    assert _disable_thinking({"provider": "nim"}) == {
        "chat_template_kwargs": {"enable_thinking": False}
    }
    assert _disable_thinking({"provider": "openai"}) is None
    assert _disable_thinking({"provider": "ollama"}) is None
