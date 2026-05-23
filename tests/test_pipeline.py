from pathlib import Path

import pytest

from parser.fusion import DualSourceFusionParser


ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


@pytest.fixture
def sample_paths():
    maker = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    mineru = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_mineru.md"
    assert maker.exists(), "maker sample missing"
    assert mineru.exists(), "mineru sample missing"
    return maker, mineru


def test_fusion_parser_produces_document(sample_paths):
    maker, mineru = sample_paths
    doc = DualSourceFusionParser().parse_files(maker, mineru)

    assert doc.meta.title
    assert doc.meta.abstract
    assert "42.29" in doc.meta.abstract.replace(" ", "") or "42." in doc.meta.abstract
    assert len(doc.references) >= 10
    assert len(doc.tables) >= 1
    assert doc.quality.maker_score > doc.quality.mineru_score
    assert doc.quality.fusion_score >= 0.6


def test_fusion_tables_prefer_mineru(sample_paths):
    maker, mineru = sample_paths
    doc = DualSourceFusionParser().parse_files(maker, mineru)
    mineru_tables = [t for t in doc.tables if t.source == "mineru"]
    assert mineru_tables, "expected mineru-sourced tables"


def test_orchestrator_runs_all_checks(sample_paths):
    from orchestrator.runner import CheckOrchestrator

    maker, mineru = sample_paths
    doc = DualSourceFusionParser().parse_files(maker, mineru)
    report = CheckOrchestrator(journal_profile="scut_natural_science", llm_enabled=False).run(
        doc, "test-job"
    )

    assert len(report.checks_run) == 4
    assert report.summary.errors + report.summary.warnings + report.summary.infos >= 1
    assert report.paper_title


def test_reference_checker_finds_entries(sample_paths):
    maker, mineru = sample_paths
    doc = DualSourceFusionParser().parse_files(maker, mineru)
    indices = {r.index for r in doc.references}
    assert 1 in indices
    assert 16 in indices or max(indices) >= 15
