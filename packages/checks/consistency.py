from __future__ import annotations

import json
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from checks.base import BaseChecker, section_text
from schema.models import CheckCategory, Issue, IssueSeverity, PaperDocument


ABBREV_PATTERN = re.compile(
    r"\b(ARIMA|SVR|RF|KNN|BiLSTM|CNN|LSTM|GRU|TCN|IDLM|ADF|RMSE|WMAPE)\b"
)
NUMERIC_PATTERN = re.compile(
    r"(\d+(?:\.\s*\d+)?(?:\s*±\s*\d+(?:\.\s*\d+)?)?)\s*(%|pcu|km/h)?",
    re.I,
)


class ConsistencyChecker(BaseChecker):
    category = CheckCategory.CONSISTENCY

    def __init__(self, llm_enabled: bool | None = None) -> None:
        if llm_enabled is None:
            llm_enabled = bool(os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"))
        self.llm_enabled = llm_enabled

    def check(self, doc: PaperDocument) -> list[Issue]:
        issues: list[Issue] = []
        abstract = doc.meta.abstract or section_text(doc, "abstract")
        experiment = section_text(doc, "experiment")
        conclusion = section_text(doc, "conclusion")
        body = "\n".join(
            b.text for b in doc.blocks if b.type.value == "paragraph"
        )

        issues.extend(self._check_abstract_numbers(abstract, experiment, conclusion))
        issues.extend(self._check_abbreviations(body))
        if self.llm_enabled and not doc.quality.degraded:
            issues.extend(self._llm_check(abstract, experiment, conclusion))
        elif not self.llm_enabled:
            issues.extend(self._rule_coverage_check(abstract))
        return issues

    def _normalize_number(self, value: str) -> str:
        return re.sub(r"\s+", "", value)

    def _number_signature(self, value: str) -> tuple[Decimal, str] | None:
        normalized = self._normalize_number(value)
        match = re.match(r"(\d+(?:\.\d+)?)", normalized)
        if not match:
            return None
        try:
            number = Decimal(match.group(1))
        except InvalidOperation:
            return None
        unit_match = re.search(r"(pcu|km/h|%)", normalized, re.I)
        unit = unit_match.group(1).lower() if unit_match else ""
        return number.normalize(), unit

    def _number_found_in_pool(self, raw: str, search_pool: str) -> bool:
        normalized = self._normalize_number(raw)
        pool_norm = self._normalize_number(search_pool)
        if normalized in pool_norm or raw in search_pool:
            return True

        target = self._number_signature(raw)
        if not target:
            return False
        target_value, target_unit = target
        for candidate in NUMERIC_PATTERN.finditer(search_pool):
            signature = self._number_signature(candidate.group(0))
            if not signature:
                continue
            value, unit = signature
            units_compatible = not target_unit or not unit or target_unit == unit
            if value == target_value and units_compatible:
                return True
        return False

    def _derived_percentage_found(self, raw: str, search_pool: str) -> bool:
        target = self._number_signature(raw)
        if not target or target[1] != "%":
            return False

        target_value = target[0]
        values: list[Decimal] = []
        seen: set[Decimal] = set()
        for candidate in NUMERIC_PATTERN.finditer(search_pool):
            signature = self._number_signature(candidate.group(0))
            if not signature:
                continue
            value, _unit = signature
            if value <= 0 or value > Decimal("10000") or value in seen:
                continue
            seen.add(value)
            values.append(value)

        tolerance = Decimal("0.25")
        for larger in values:
            for smaller in values:
                if larger <= smaller:
                    continue
                reduction = (larger - smaller) / larger * Decimal("100")
                if abs(reduction - target_value) <= tolerance:
                    return True
        return False

    def _check_abstract_numbers(
        self, abstract: str, experiment: str, conclusion: str
    ) -> list[Issue]:
        issues: list[Issue] = []
        if not abstract:
            return issues

        search_pool = f"{experiment}\n{conclusion}"
        for match in NUMERIC_PATTERN.finditer(abstract):
            raw = match.group(0)
            if "%" not in raw and "pcu" not in raw.lower():
                continue
            normalized = self._normalize_number(raw)
            context = abstract[max(0, match.start() - 20) : match.end() + 20]
            derived_ok = (
                "%" in raw
                and any(word in context for word in ["降低", "提高", "提升", "下降", "减少", "增大"])
                and self._derived_percentage_found(raw, search_pool)
            )
            if not (self._number_found_in_pool(raw, search_pool) or derived_ok):
                issues.append(
                    Issue(
                        code="CONSIST_ABSTRACT_NUMBER",
                        category=self.category,
                        severity=IssueSeverity.WARNING
                        if len(normalized) < 4
                        else IssueSeverity.ERROR,
                        section="abstract",
                        message=f"摘要中的数值「{raw.strip()}」在实验/结论章节未找到对应表述",
                        suggestion="核对摘要数据与正文实验结果是否一致",
                        evidence=raw.strip(),
                    )
                )
        return issues

    def _check_abbreviations(self, body: str) -> list[Issue]:
        issues: list[Issue] = []
        for abbrev in ABBREV_PATTERN.findall(body):
            pattern = rf"{abbrev}\s*[（(][^）)]+[）)]"
            if abbrev in {"RMSE", "WMAPE", "ADF", "IDLM"}:
                first_pos = body.find(abbrev)
                before = body[max(0, first_pos - 80) : first_pos + len(abbrev) + 40]
                if not re.search(pattern, before) and first_pos >= 0:
                    issues.append(
                        Issue(
                            code="CONSIST_ABBREV_UNDEFINED",
                            category=self.category,
                            severity=IssueSeverity.INFO,
                            message=f"缩写 {abbrev} 首次出现附近未检测到全称定义",
                            evidence=before[:100],
                        )
                    )
        return issues

    def _rule_coverage_check(self, abstract: str) -> list[Issue]:
        issues: list[Issue] = []
        required_aspects = {
            "问题/背景": any(k in abstract for k in ["针对", "问题", "不足", "隧道", "交通"]),
            "方法": any(k in abstract for k in ["模型", "网络", "方法", "CNN", "LSTM", "TCN"]),
            "数据": any(k in abstract for k in ["数据", "隧道", "流量", "实验"]),
            "结果": any(k in abstract for k in ["误差", "RMSE", "WMAPE", "结果", "降低"]),
            "结论": any(k in abstract for k in ["结果", "基础", "提供", "理论"]),
        }
        for aspect, ok in required_aspects.items():
            if not ok:
                issues.append(
                    Issue(
                        code="CONSIST_ABSTRACT_COVERAGE",
                        category=self.category,
                        severity=IssueSeverity.WARNING,
                        section="abstract",
                        message=f"摘要可能未充分覆盖：{aspect}",
                        suggestion="补充摘要中对应要素（规则检测，未启用 LLM）",
                    )
                )
        return issues

    def _llm_check(
        self, abstract: str, experiment: str, conclusion: str
    ) -> list[Issue]:
        prompt = {
            "task": "paper_consistency",
            "abstract": abstract[:2000],
            "experiment_excerpt": experiment[:3000],
            "conclusion_excerpt": conclusion[:2000],
            "output_schema": {
                "coverage_gaps": ["string"],
                "unsupported_claims": [
                    {"claim": "string", "reason": "string", "evidence_needed": "string"}
                ],
            },
        }
        try:
            data = self._call_llm(json.dumps(prompt, ensure_ascii=False))
        except Exception as exc:
            return [
                Issue(
                    code="CONSIST_LLM_UNAVAILABLE",
                    category=self.category,
                    severity=IssueSeverity.INFO,
                    message=f"LLM 语义检查跳过：{exc}",
                )
            ]

        issues: list[Issue] = []
        for gap in data.get("coverage_gaps", []):
            issues.append(
                Issue(
                    code="CONSIST_LLM_COVERAGE",
                    category=self.category,
                    severity=IssueSeverity.WARNING,
                    section="abstract",
                    message=f"摘要覆盖不足：{gap}",
                )
            )
        for item in data.get("unsupported_claims", []):
            issues.append(
                Issue(
                    code="CONSIST_LLM_CLAIM",
                    category=self.category,
                    severity=IssueSeverity.WARNING,
                    section="conclusion",
                    message=item.get("claim", "结论表述可能缺少实验支撑"),
                    suggestion=item.get("reason", ""),
                    evidence=item.get("evidence_needed", ""),
                )
            )
        return issues

    def _call_llm(self, user_content: str) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        if not api_key:
            raise RuntimeError("missing API key")

        system = (
            "你是论文预检查助手。仅返回 JSON，不要 markdown。"
            "评估摘要是否覆盖问题/方法/数据/结果/结论，"
            "并找出结论中可能缺少实验支撑的 claim。"
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
