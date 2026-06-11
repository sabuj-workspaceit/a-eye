from __future__ import annotations

import ast
import operator

from sqlalchemy.orm import Session

from app.db.models.rule import Rule
from app.db.models.zone_region import ZoneRegion

OPERATORS = {
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


def safe_eval_condition(condition: str, context: dict[str, object]) -> bool:
    node = ast.parse(condition, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            raise ValueError(f"Unsupported binary operator: {node.op}")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Not):
                return not operand
            raise ValueError(f"Unsupported unary operator: {node.op}")
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for val in node.values:
                    if not _eval(val):
                        return False
                return True
            if isinstance(node.op, ast.Or):
                for val in node.values:
                    if _eval(val):
                        return True
                return False
            raise ValueError(f"Unsupported boolean operator: {node.op}")
        if isinstance(node, ast.Compare):
            left = _eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = _eval(comparator)
                if not OPERATORS[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            raise NameError(f"Unknown variable: {node.id}")
        if isinstance(node, ast.Constant):
            return node.value
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    return bool(_eval(node))


def evaluate_rules(scan_type: str, zone_features: dict[str, dict[str, object]], db: Session) -> list[dict[str, object]]:
    rules = db.query(Rule).filter(Rule.scan_type == scan_type).all()
    findings: list[dict[str, object]] = []
    for rule in rules:
        zone_region = rule.zone_region
        if not zone_region:
            continue
        zone_name = zone_region.name
        features = zone_features.get(zone_name)
        if not features or "error" in features:
            continue
        context = {**features}
        if isinstance(features.get("average_color"), dict):
            context.update(features["average_color"])
        if isinstance(features.get("texture_metrics"), dict):
            context.update(features["texture_metrics"])
        if isinstance(features.get("spots"), dict):
            context.update(features["spots"])
        if isinstance(features.get("cracks"), dict):
            context.update(features["cracks"])
            
        try:
            if safe_eval_condition(rule.condition, context):
                findings.append(
                    {
                        "rule_id": rule.id,
                        "zone_name": zone_name,
                        "condition": rule.condition,
                        "finding": rule.finding,
                        "notes": rule.description or "",
                        "severity": rule.severity or "medium",
                        "scan_type": rule.scan_type,
                    }
                )
        except Exception:
            continue
    return findings
