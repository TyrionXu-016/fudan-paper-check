from orchestrator.issue_enricher import enrich_issues
from orchestrator.runner import CheckOrchestrator
from parser.fusion import DualSourceFusionParser
from parser.span_builder import build_spans
from pathlib import Path

from schema.models import CheckCategory, Issue, IssueSeverity

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def test_enrich_issues_adds_ids_and_span():
    maker = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    doc = DualSourceFusionParser().parse_files(maker, None)
    spans = build_spans(doc)
    report = CheckOrchestrator(journal_profile="generic", llm_enabled=False).run(
        doc, "test-job"
    )
    enriched = enrich_issues(report.issues, doc, spans)
    assert enriched
    for issue in enriched:
        assert issue.id
        assert issue.issue_type is not None


def test_enrich_issues_leaves_span_empty_without_confident_match():
    maker = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    doc = DualSourceFusionParser().parse_files(maker, None)
    spans = build_spans(doc)
    issue = Issue(
        code="NO_MATCH",
        category=CheckCategory.FORMAT,
        severity=IssueSeverity.WARNING,
        message="没有可定位证据的问题",
    )

    enriched = enrich_issues([issue], doc, spans)

    assert enriched[0].span_id is None
