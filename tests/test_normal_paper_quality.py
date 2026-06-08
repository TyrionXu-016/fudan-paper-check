from pathlib import Path

from checks.consistency import ConsistencyChecker
from checks.format import FormatChecker
from checks.structure import StructureChecker
from parser.fusion import DualSourceFusionParser
from schema.models import (
    Block,
    BlockType,
    CheckCategory,
    Issue,
    IssueSeverity,
    PaperDocument,
    PaperMeta,
    Section,
    SectionKind,
)


ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
SCUT_SAMPLE = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"


def _codes(issues):
    return {issue.code for issue in issues}


def test_scut_keywords_are_not_reported_as_missing_or_success_issue():
    doc = DualSourceFusionParser().parse(SCUT_SAMPLE.read_text(encoding="utf-8"))

    issues = StructureChecker("scut_natural_science").check(doc)

    assert doc.meta.keywords
    assert not [
        issue
        for issue in issues
        if issue.code == "STRUCT_MISSING_SECTION" and issue.section == "keywords"
    ]
    assert "STRUCT_KEYWORDS_OK" not in _codes(issues)


def test_scut_parser_finds_non_markdown_figure_and_table_captions():
    doc = DualSourceFusionParser().parse(SCUT_SAMPLE.read_text(encoding="utf-8"))

    figure_numbers = {figure.number for figure in doc.figures}
    table_numbers = {table.number for table in doc.tables}

    assert 5 in figure_numbers
    assert {1, 4}.issubset(table_numbers)

    issues = StructureChecker("scut_natural_science").check(doc)
    missing_anchors = {
        issue.evidence
        for issue in issues
        if issue.code in {"STRUCT_FIGURE_REF_MISSING", "STRUCT_TABLE_REF_MISSING"}
    }
    assert "图 5" not in missing_anchors
    assert "表 1" not in missing_anchors
    assert "表 4" not in missing_anchors


def test_scut_ocr_spaced_doi_matches_journal_pattern():
    doc = DualSourceFusionParser().parse(SCUT_SAMPLE.read_text(encoding="utf-8"))

    issues = FormatChecker("scut_natural_science").check(doc)

    assert "FORMAT_DOI_PATTERN" not in _codes(issues)


def test_abstract_numbers_match_body_values_with_uncertainty():
    body = "实验结果显示，RMSE 为 42.29±5.66 pcu，WMAPE 为 4.18 ± 1.06%。"
    doc = PaperDocument(
        meta=PaperMeta(abstract="摘要显示，RMSE 为 42. 29 pcu，WMAPE 为 4. 18%。"),
        sections=[
            Section(
                id="sec_experiment",
                kind=SectionKind.EXPERIMENT,
                title="3 实验分析",
                start_line=1,
                end_line=1,
            )
        ],
        blocks=[
            Block(
                id="blk_1",
                type=BlockType.PARAGRAPH,
                section_id="sec_experiment",
                line_start=1,
                line_end=1,
                text=body,
                raw=body,
            )
        ],
    )

    issues = ConsistencyChecker(llm_enabled=False).check(doc)

    assert "CONSIST_ABSTRACT_NUMBER" not in _codes(issues)


def test_scut_sample_abstract_numbers_are_supported_by_experiment_sections():
    doc = DualSourceFusionParser().parse(SCUT_SAMPLE.read_text(encoding="utf-8"))

    issues = ConsistencyChecker(llm_enabled=False).check(doc)

    assert "CONSIST_ABSTRACT_NUMBER" not in _codes(issues)


def test_parser_recognizes_bare_english_frontmatter_sections():
    content = """
public_cs_master_thesis

Abstract
This thesis studies Chinese font style transfer with neural networks.

Keywords
font transfer; neural network

1 Introduction
The introduction describes the research problem.

Bibliography
- [1] Doe J. Neural font transfer. Journal, 2017.
""".strip()

    doc = DualSourceFusionParser().parse(content)
    kinds = {section.kind for section in doc.sections}

    assert SectionKind.ABSTRACT in kinds
    assert SectionKind.KEYWORDS in kinds
    assert SectionKind.REFERENCES in kinds
    assert doc.meta.abstract.startswith("This thesis studies")
    assert doc.meta.keywords == ["font transfer", "neural network"]
    assert doc.references


def test_reference_section_text_is_not_reported_as_empty():
    doc = PaperDocument(
        sections=[
            Section(
                id="sec_refs",
                kind=SectionKind.REFERENCES,
                title="Bibliography",
                start_line=1,
                end_line=2,
            )
        ],
        blocks=[
            Block(
                id="blk_ref",
                type=BlockType.PARAGRAPH,
                section_id="sec_refs",
                line_start=2,
                line_end=2,
                text="Doe J. Neural font transfer. Journal, 2017.",
                raw="Doe J. Neural font transfer. Journal, 2017.",
            )
        ],
    )

    issues = StructureChecker("generic").check(doc)

    assert "STRUCT_EMPTY_REFERENCES" not in _codes(issues)


def test_plain_english_references_are_structured_sequentially():
    content = """
Title

Bibliography
Doe J. Neural font transfer. Journal, 2017.
Smith A. Deep learning for glyphs. Conference, 2018.
""".strip()

    doc = DualSourceFusionParser().parse(content)

    assert [ref.index for ref in doc.references] == [1, 2]
    assert doc.references[0].raw_text.startswith("Doe J.")


def test_ocr_number_space_warning_is_aggregated_and_ignores_doi():
    doc = PaperDocument(
        meta=PaperMeta(doi="10. 12141/j. issn. 1000-565X. 250274"),
        blocks=[
            Block(
                id="blk_1",
                type=BlockType.PARAGRAPH,
                section_id="sec_other",
                line_start=1,
                line_end=1,
                text="doi:10. 12141/j. issn. 1000-565X. 250274",
                raw="doi:10. 12141/j. issn. 1000-565X. 250274",
            ),
            Block(
                id="blk_2",
                type=BlockType.PARAGRAPH,
                section_id="sec_other",
                line_start=2,
                line_end=2,
                text="RMSE 为 42. 29，WMAPE 为 4. 18%。",
                raw="RMSE 为 42. 29，WMAPE 为 4. 18%。",
            ),
        ],
    )

    ocr_issues = [
        issue
        for issue in FormatChecker("scut_natural_science").check(doc)
        if issue.code == "FORMAT_OCR_NUMBER_SPACE"
    ]

    assert len(ocr_issues) == 1
    assert "42. 29" in ocr_issues[0].evidence
    assert "10. 12141" not in ocr_issues[0].evidence


def test_abbreviation_definition_accepts_full_name_before_abbrev():
    body = (
        "本文提出一种集成深度学习模型(Integrated Deep Learning Model, IDLM)，"
        "随后使用 IDLM 进行预测。"
    )
    doc = PaperDocument(
        blocks=[
            Block(
                id="blk_1",
                type=BlockType.PARAGRAPH,
                section_id="sec_other",
                line_start=1,
                line_end=1,
                text=body,
                raw=body,
            )
        ],
    )

    issues = ConsistencyChecker(llm_enabled=False).check(doc)

    assert "CONSIST_ABBREV_UNDEFINED" not in _codes(issues)


def test_abbreviation_definition_accepts_abbrev_before_chinese_descriptor():
    body = "利用 ADF 平稳性检验将流量数据划分为平稳和非平稳序列。"
    doc = PaperDocument(
        blocks=[
            Block(
                id="blk_1",
                type=BlockType.PARAGRAPH,
                section_id="sec_other",
                line_start=1,
                line_end=1,
                text=body,
                raw=body,
            )
        ],
    )

    issues = ConsistencyChecker(llm_enabled=False).check(doc)

    assert "CONSIST_ABBREV_UNDEFINED" not in _codes(issues)


def test_legacy_llm_issue_type_is_loaded_as_logic_issue():
    issue = Issue.model_validate(
        {
            "issue_type": "llm",
            "code": "LEGACY_LLM",
            "category": CheckCategory.CONSISTENCY,
            "severity": IssueSeverity.INFO,
            "message": "legacy issue",
        }
    )

    assert issue.issue_type and issue.issue_type.value == "logic_contradiction"
