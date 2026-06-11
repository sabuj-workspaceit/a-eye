"""
Unit tests for the rule engine module.
"""

import pytest

from app.services.rule_engine import safe_eval_condition


class TestRuleEvaluation:
    """Tests for the rule evaluation functions."""

    def test_evaluate_condition_true(self):
        """Test evaluating a condition that should return True."""
        condition = "0.8 > 0.5"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_condition_false(self):
        """Test evaluating a condition that should return False."""
        condition = "0.3 > 0.5"
        result = safe_eval_condition(condition, {})
        assert result is False

    def test_evaluate_simple_gt_operator(self):
        """Test greater than operator."""
        condition = "15 > 10"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_simple_lt_operator(self):
        """Test less than operator."""
        condition = "5 < 10"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_equality_operator(self):
        """Test equality operator."""
        condition = "10 == 10"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_gte_operator(self):
        """Test greater than or equal operator."""
        condition = "10 >= 10"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_lte_operator(self):
        """Test less than or equal operator."""
        condition = "10 <= 10"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_not_equal_operator(self):
        """Test not equal operator."""
        condition = "10 != 5"
        result = safe_eval_condition(condition, {})
        assert result is True

    def test_evaluate_and_operator(self):
        """Test logical AND operator."""
        condition = "redness > 0.7 and brightness < 0.5"
        context = {"redness": 0.8, "brightness": 0.3}
        result = safe_eval_condition(condition, context)
        assert result is True

        condition = "redness > 0.7 and brightness < 0.5"
        context = {"redness": 0.6, "brightness": 0.3}
        result = safe_eval_condition(condition, context)
        assert result is False

    def test_evaluate_or_operator(self):
        """Test logical OR operator."""
        condition = "redness > 0.7 or brightness < 0.5"
        context = {"redness": 0.6, "brightness": 0.3}
        result = safe_eval_condition(condition, context)
        assert result is True

        condition = "redness > 0.7 or brightness < 0.5"
        context = {"redness": 0.6, "brightness": 0.6}
        result = safe_eval_condition(condition, context)
        assert result is False

    def test_evaluate_not_operator(self):
        """Test logical NOT operator."""
        condition = "not cracks"
        context = {"cracks": False}
        result = safe_eval_condition(condition, context)
        assert result is True

        condition = "not cracks"
        context = {"cracks": True}
        result = safe_eval_condition(condition, context)
        assert result is False

