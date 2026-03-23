"""tests/test_compliance.py — Unit tests for compliance.py (no API key required)."""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import compliance


class TestGetAiDisclosure:
    def test_returns_string(self):
        result = compliance.get_ai_disclosure("description")
        assert isinstance(result, str)
        assert len(result) > 10

    def test_different_formats(self):
        desc = compliance.get_ai_disclosure("description")
        pinned = compliance.get_ai_disclosure("pinned_comment")
        assert isinstance(desc, str)
        assert isinstance(pinned, str)

    def test_unknown_format_returns_something(self):
        result = compliance.get_ai_disclosure("unknown_format")
        assert isinstance(result, str)


class TestCheckMusicLicense:
    def test_known_safe_source(self):
        result = compliance.check_music_license("YouTube Audio Library")
        assert result["safe"] is True

    def test_unknown_source(self):
        result = compliance.check_music_license("some random soundcloud track")
        assert "safe" in result
        assert "note" in result or "warning" in result or "message" in result

    def test_returns_dict(self):
        result = compliance.check_music_license("Epidemic Sound")
        assert isinstance(result, dict)


class TestCheckScriptPolicy:
    def test_clean_script_low_risk(self):
        script = "Today we're going to learn about the history of ancient Rome. The Roman Empire was founded in 27 BC."
        result = compliance.check_script_policy(script)
        assert "risk_score" in result
        assert result["risk_score"] < 50

    def test_returns_required_keys(self):
        result = compliance.check_script_policy("Hello world")
        assert "risk_score" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_empty_script(self):
        result = compliance.check_script_policy("")
        assert isinstance(result, dict)
