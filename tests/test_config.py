"""tests/test_config.py — Unit tests for config.py (no API key required)."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMissingKeys:
    def test_missing_keys_returns_list(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
        monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "")
        monkeypatch.setattr(config, "ELEVENLABS_VOICE_ID", "")
        monkeypatch.setattr(config, "OPENAI_API_KEY", "")
        monkeypatch.setattr(config, "PEXELS_API_KEY", "")
        missing = config.missing_keys()
        assert isinstance(missing, list)
        assert "ANTHROPIC_API_KEY" in missing

    def test_no_missing_when_all_set(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "el-test")
        monkeypatch.setattr(config, "ELEVENLABS_VOICE_ID", "voice-id")
        monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-openai")
        monkeypatch.setattr(config, "PEXELS_API_KEY", "pexels-key")
        missing = config.missing_keys()
        assert missing == []

    def test_partial_missing(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.setattr(config, "ELEVENLABS_API_KEY", "")
        monkeypatch.setattr(config, "ELEVENLABS_VOICE_ID", "voice-id")
        monkeypatch.setattr(config, "OPENAI_API_KEY", "sk-openai")
        monkeypatch.setattr(config, "PEXELS_API_KEY", "pexels-key")
        missing = config.missing_keys()
        assert "ELEVENLABS_API_KEY" in missing
        assert "ANTHROPIC_API_KEY" not in missing


class TestPaths:
    def test_base_dir_exists(self):
        import config
        assert config.BASE_DIR.exists()

    def test_outputs_dir_created(self):
        import config
        assert config.OUTPUTS_DIR.exists()
