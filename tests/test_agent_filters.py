import pytest
from agents.post_filters import apply_typo_grammar_filters
from schema.models import Issue, IssueType, CheckCategory, IssueSeverity

def test_apply_typo_grammar_filters():
    span_text = "本文使用 CNN 模型和 [1, 2] 参考文献，结果是 42.5%"
    
    issues = [
        # 1. 成功案例：修改普通词语，不影响白名单、数字和引用
        Issue(
            code="T1",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="错别字",
            original_text="模型和",
            suggested_text="模型与",
            issue_type=IssueType.TYPO,
        ),
        # 2. 失败案例：original_text 不在 span_text 中
        Issue(
            code="T2",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="错别字",
            original_text="支持向量机",
            suggested_text="SVM",
            issue_type=IssueType.TYPO,
        ),
        # 3. 失败案例：数字被篡改
        Issue(
            code="T3",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="错别字",
            original_text="结果是 42.5%",
            suggested_text="结果是 42.6%",
            issue_type=IssueType.TYPO,
        ),
        # 4. 失败案例：引用标记被篡改
        Issue(
            code="T4",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="错别字",
            original_text="模型和 [1, 2] 参考文献",
            suggested_text="模型和 [1] 参考文献",
            issue_type=IssueType.TYPO,
        ),
        # 5. 失败案例：白名单词汇被替换
        Issue(
            code="T5",
            category=CheckCategory.FORMAT,
            severity=IssueSeverity.WARNING,
            message="错别字",
            original_text="使用 CNN 模型",
            suggested_text="使用 卷积神经网络 模型",
            issue_type=IssueType.TYPO,
        ),
    ]
    
    valid_issues = apply_typo_grammar_filters(issues, span_text)
    
    assert len(valid_issues) == 1
    assert valid_issues[0].code == "T1"
