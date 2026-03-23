"""tests/test_seo.py — Unit tests for seo.py (no API key required)."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seo


class TestGetCpmTable:
    def test_returns_dict(self):
        table = seo.get_cpm_table()
        assert isinstance(table, dict)

    def test_has_finance(self):
        table = seo.get_cpm_table()
        assert "Finance & Investing" in table

    def test_entry_has_required_keys(self):
        table = seo.get_cpm_table()
        for niche, data in table.items():
            assert "cpm" in data, f"Missing 'cpm' for niche: {niche}"
            assert "rpm" in data, f"Missing 'rpm' for niche: {niche}"
            assert "competition" in data, f"Missing 'competition' for niche: {niche}"

    def test_roblox_present(self):
        table = seo.get_cpm_table()
        assert "Roblox Gaming" in table

    def test_all_niches_have_string_values(self):
        table = seo.get_cpm_table()
        for niche, data in table.items():
            assert isinstance(data["cpm"], str)
            assert isinstance(data["rpm"], str)
            assert isinstance(data["competition"], str)


class TestGenerateSeoPackageMissingKey:
    def test_missing_api_key_returns_error(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
        result = seo.generate_seo_package("test topic", "test title", "facts")
        assert result["success"] is False
        assert "error" in result
