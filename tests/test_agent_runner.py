import pytest
from orchestrator.agent_runner import merge_issues
from schema.models import Issue, IssueSeverity, CheckCategory, IssueType

def test_merge_issues():
    issues = [
        # 同 span_id, 同 type
        Issue(
            code="R1",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.INFO,
            message="规则提示 1",
            span_id="span_1",
            issue_type=IssueType.FORMAT
        ),
        Issue(
            code="A1",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="Agent 提示 1",
            span_id="span_1",
            issue_type=IssueType.FORMAT
        ),
        # 同 span_id, 不同 type
        Issue(
            code="A2",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.ERROR,
            message="错别字",
            span_id="span_1",
            issue_type=IssueType.TYPO
        ),
        # 无 span_id 或 type
        Issue(
            code="R2",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="全局问题"
        )
    ]
    
    merged = merge_issues(issues)
    
    # 应该有 3 个 issue (span_1 的 FORMAT 合并为一个)
    assert len(merged) == 3
    
    # 寻找合并后的 span_1 FORMAT issue
    format_issue = next(i for i in merged if i.span_id == "span_1" and i.issue_type == IssueType.FORMAT)
    assert format_issue.severity == IssueSeverity.WARNING # 继承更高优先级
    assert "规则提示 1" in format_issue.message
    assert "Agent 提示 1" in format_issue.message
    
    # 其他的应该保留
    assert any(i.issue_type == IssueType.TYPO for i in merged)
    assert any(i.code == "R2" for i in merged)
