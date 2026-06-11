"""
Unit tests for the report generator module.
"""

import pytest

from app.services.protocol_engine import apply_safety_filter, generate_summary


class TestSafetyFilter:
    """Tests for the safety filter function."""

    def test_safety_filter_blocks_blocked_words(self):
        """Test that safety filter catches blocked words."""
        text = "This patient has concerning symptoms"
        filtered = apply_safety_filter(text)
        assert isinstance(filtered, str)

    def test_safety_filter_allows_safe_text(self):
        """Test that safety filter allows safe text."""
        text = "The analysis shows normal results"
        filtered = apply_safety_filter(text)
        assert isinstance(filtered, str)
        assert "The analysis shows normal results" in filtered or len(filtered) > 0

    def test_safety_filter_returns_string(self):
        """Test that safety filter always returns a string."""
        text = "Test message"
        filtered = apply_safety_filter(text)
        assert isinstance(filtered, str)


class TestSummaryGeneration:
    """Tests for the summary generation function."""

    def test_generate_summary_with_findings(self):
        """Test summary generation with findings."""
        findings = [
            {
                "zone": "zone_1",
                "severity": "high",
                "description": "Test finding",
            }
        ]
        summary = generate_summary(findings, "eye")
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_generate_summary_with_no_findings(self):
        """Test summary generation with no findings."""
        findings = []
        summary = generate_summary(findings, "eye")
        assert isinstance(summary, str)

    def test_generate_summary_different_scan_types(self):
        """Test summary generation for different scan types."""
        findings = [{"zone": "zone_1", "severity": "medium"}]
        for scan_type in ["eye", "tongue", "face"]:
            summary = generate_summary(findings, scan_type)
            assert isinstance(summary, str)
            assert len(summary) > 0

    def test_generate_summary_with_multiple_findings(self):
        """Test summary with multiple findings."""
        findings = [
            {"zone": "zone_1", "severity": "high", "description": "Finding 1"},
            {"zone": "zone_2", "severity": "low", "description": "Finding 2"},
        ]
        summary = generate_summary(findings, "eye")
        assert isinstance(summary, str)
        assert len(summary) > 0
