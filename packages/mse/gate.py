from __future__ import annotations

from pathlib import Path

import yaml

from mse.models import GateDecision
from schema.models import Issue, IssueSeverity

DEFAULT_GATE = {
    "max_errors": 0,
    "max_warnings": 5,
    "required_sections": ["abstract", "references"],
}


def load_gate_config(path: str | None = None) -> dict:
    config_path = Path(path or "config/mse/gate.yaml")
    if not config_path.exists():
        return dict(DEFAULT_GATE)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    merged = dict(DEFAULT_GATE)
    merged.update(data)
    return merged


def evaluate_gate(
    round_id: str,
    issues: list[Issue],
    *,
    config: dict | None = None,
) -> GateDecision:
    cfg = config or load_gate_config()
    errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
    warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

    if errors > cfg["max_errors"]:
        return GateDecision(
            round_id=round_id,
            passed=False,
            reason=f"error_count={errors} exceeds max {cfg['max_errors']}",
            notify_target="student",
        )
    if warnings > cfg["max_warnings"]:
        return GateDecision(
            round_id=round_id,
            passed=False,
            reason=f"warning_count={warnings} exceeds max {cfg['max_warnings']}",
            notify_target="student",
        )
    return GateDecision(
        round_id=round_id,
        passed=True,
        reason="gate passed",
        notify_target="advisor",
    )
