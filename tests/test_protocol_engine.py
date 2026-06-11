import pytest
from app.services.protocol_engine import apply_safety_filter

class TestProtocolEngine:
    def test_safety_filter_redacts_blocked_words(self):
        text = "This is a medical emergency and needs urgent treatment to cure the disease."
        filtered = apply_safety_filter(text)
        assert "medical" not in filtered
        assert "emergency" not in filtered
        assert "urgent" not in filtered
        assert "treatment" not in filtered
        assert "cure" not in filtered
        assert "disease" not in filtered
        assert "[REDACTED]" in filtered
        assert filtered.count("[REDACTED]") == 6

    def test_safety_filter_clean_text(self):
        text = "This is a wellness recommendation to stay hydrated."
        filtered = apply_safety_filter(text)
        assert filtered == text
