from __future__ import annotations

from pathlib import Path

import yaml

from schema.models import RuleBaseDetail, RuleBaseListItem, RuleBaseSummary

_ROOT = Path(__file__).resolve().parents[2]
_JOURNALS_DIR = _ROOT / "config" / "journals"

_DEFAULT_SUMMARY = RuleBaseSummary(
    format="章节结构、摘要关键词、图表公式编号等格式规范",
    reference="参考文献引用标注与著录格式（GB/T 7714）",
    typo="错别字与拼写（Agent 检测）",
    grammar="语病与句式（Agent 检测）",
    polish="学术语体与润色建议（Agent 检测）",
    logic="摘要-正文一致性与逻辑矛盾（Agent 检测）",
)


def _journals_dir() -> Path:
    return _JOURNALS_DIR


def list_rule_base_ids() -> list[str]:
    directory = _journals_dir()
    if not directory.exists():
        return ["generic"]
    ids = sorted(p.stem for p in directory.glob("*.yaml"))
    return ids or ["generic"]


def load_rule_base_yaml(rule_base_id: str) -> dict:
    path = _journals_dir() / f"{rule_base_id}.yaml"
    if not path.exists():
        path = _journals_dir() / "generic.yaml"
    if not path.exists():
        return {"name": rule_base_id, "display_name": rule_base_id}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("name", rule_base_id)
    return data


def _parse_summary(raw: dict | None) -> RuleBaseSummary:
    if not raw:
        return _DEFAULT_SUMMARY.model_copy()
    merged = _DEFAULT_SUMMARY.model_dump()
    merged.update({k: v for k, v in raw.items() if v})
    return RuleBaseSummary.model_validate(merged)


def get_rule_base(rule_base_id: str) -> RuleBaseDetail | None:
    path = _journals_dir() / f"{rule_base_id}.yaml"
    if not path.exists():
        if rule_base_id != "generic":
            return None
    data = load_rule_base_yaml(rule_base_id)
    return RuleBaseDetail(
        id=data.get("name", rule_base_id),
        display_name=data.get("display_name", rule_base_id),
        summary=_parse_summary(data.get("summary")),
        required_sections=list(data.get("required_sections") or []),
        optional_sections=list(data.get("optional_sections") or []),
    )


def list_rule_bases() -> list[RuleBaseListItem]:
    items: list[RuleBaseListItem] = []
    for rule_id in list_rule_base_ids():
        detail = get_rule_base(rule_id)
        if detail:
            items.append(
                RuleBaseListItem(
                    id=detail.id,
                    display_name=detail.display_name,
                    summary=detail.summary,
                )
            )
    return items
