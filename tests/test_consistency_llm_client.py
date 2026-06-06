from __future__ import annotations

from checks.consistency import ConsistencyChecker
from schema.models import (
    Block,
    BlockType,
    PaperDocument,
    Section,
    SectionKind,
)


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def is_available(self) -> bool:
        return True

    def complete_json(self, system: str, user: str, **kwargs) -> dict:
        self.calls.append((system, user, kwargs))
        return {
            "coverage_gaps": ["缺少结果摘要"],
            "unsupported_claims": [
                {
                    "claim": "结论表述过强",
                    "reason": "实验支撑不足",
                    "evidence_needed": "补充消融实验",
                }
            ],
        }


def _doc() -> PaperDocument:
    sections = [
        Section(id="abs", kind=SectionKind.ABSTRACT, title="摘要", start_line=1, end_line=3),
        Section(id="exp", kind=SectionKind.EXPERIMENT, title="实验", start_line=4, end_line=6),
        Section(id="con", kind=SectionKind.CONCLUSION, title="结论", start_line=7, end_line=9),
    ]
    blocks = [
        Block(
            id="b1",
            type=BlockType.PARAGRAPH,
            section_id="abs",
            line_start=1,
            line_end=3,
            text="摘要：本文提出一种模型。",
        ),
        Block(
            id="b2",
            type=BlockType.PARAGRAPH,
            section_id="exp",
            line_start=4,
            line_end=6,
            text="实验显示模型可运行。",
        ),
        Block(
            id="b3",
            type=BlockType.PARAGRAPH,
            section_id="con",
            line_start=7,
            line_end=9,
            text="结论表述过强。",
        ),
    ]
    return PaperDocument(sections=sections, blocks=blocks)


def test_consistency_checker_uses_injected_llm_client() -> None:
    client = FakeLLMClient()

    issues = ConsistencyChecker(client=client).check(_doc())

    assert client.calls
    assert {issue.code for issue in issues} >= {
        "CONSIST_LLM_COVERAGE",
        "CONSIST_LLM_CLAIM",
    }
