from __future__ import annotations

import os
from collections import defaultdict
from typing import Callable

from agents.base import AgentContext, LLMClient, DocRetriever, RuleRetriever
from agents.format_agent import FormatAgent
from agents.structure_agent import StructureAgent
from agents.reference_agent import ReferenceAgent
from agents.typo_agent import TypoAgent
from agents.grammar_agent import GrammarAgent
from agents.logic_agent import LogicAgent
from agents.polish_agent import PolishAgent

from orchestrator.runner import CheckOrchestrator
from schema.models import CheckCategory, CheckReport, DetectStage, Issue, IssueSeverity, PaperDocument, Span


def merge_issues(issues: list[Issue]) -> list[Issue]:
    """
    Merge issues with the same span_id and issue_type.
    Keep the highest severity, merge messages.
    """
    severity_rank = {IssueSeverity.ERROR: 3, IssueSeverity.WARNING: 2, IssueSeverity.INFO: 1}
    
    # grouped by (span_id, issue_type)
    grouped = defaultdict(list)
    result = []
    
    for issue in issues:
        if not issue.span_id or not issue.issue_type:
            result.append(issue)
            continue
            
        grouped[(issue.span_id, issue.issue_type)].append(issue)
        
    for group_key, group_issues in grouped.items():
        if len(group_issues) == 1:
            result.append(group_issues[0])
            continue
            
        # Sort by severity descending
        group_issues.sort(key=lambda x: severity_rank.get(x.severity, 0), reverse=True)
        
        primary = group_issues[0]
        merged_message = " | ".join([i.message for i in group_issues if i.message])
        
        primary.message = merged_message
        result.append(primary)
        
    return result


class AgentRunner:
    def __init__(self, journal_profile: str = "generic"):
        self.journal_profile = journal_profile
        self.mode = os.getenv("AGENT_MODE", "rules").lower()
        
    def run(
        self, 
        doc: PaperDocument, 
        spans: list[Span], 
        job_id: str, 
        on_progress: Callable[[DetectStage, int, str], None] | None = None
    ) -> CheckReport:
        rule_issues = []
        checks_run = []
        
        # 1. Run Rules if mode is rules or hybrid
        if self.mode in ("rules", "hybrid"):
            orchestrator = CheckOrchestrator(journal_profile=self.journal_profile)
            report = orchestrator.run(doc, job_id, on_progress=on_progress)
            rule_issues = report.issues
            checks_run.extend(report.checks_run)
            
        agent_issues = []
        
        # 2. Run Agents if mode is agents or hybrid
        if self.mode in ("agents", "hybrid"):
            ctx = AgentContext(
                task_id=job_id,
                rule_base_id=self.journal_profile,
                rule_retriever=RuleRetriever(self.journal_profile),
                doc_retriever=DocRetriever(job_id),
                llm=LLMClient(),
                publish_progress=on_progress or (lambda s, p, m: None),
                config={}
            )
            
            agents = []
            
            # In hybrid mode, we might skip Agent-1 if rules are run. But we'll run it for now.
            if self.mode == "agents":
                agents.extend([FormatAgent(), StructureAgent(), ReferenceAgent()])
                
            agents.extend([
                TypoAgent(),
                GrammarAgent(),
                LogicAgent(),
                PolishAgent()
            ])
            
            total_agents = len(agents)
            for i, agent in enumerate(agents):
                if on_progress:
                    on_progress(agent.stage, int(40 + (i / total_agents) * 50), f"Running {agent.name}...")
                
                new_issues = agent.run(doc, spans, ctx)
                agent_issues.extend(new_issues)
                
        # 3. Merge
        all_issues = rule_issues + agent_issues
        merged = merge_issues(all_issues)
        
        # 4. Generate Report summary
        from orchestrator.runner import CheckReport, ReportSummary
        summary = ReportSummary()
        for iss in merged:
            if iss.severity == IssueSeverity.ERROR:
                summary.errors += 1
            elif iss.severity == IssueSeverity.WARNING:
                summary.warnings += 1
            else:
                summary.infos += 1
                
        return CheckReport(
            job_id=job_id,
            parse_quality=doc.quality,
            summary=summary,
            issues=merged,
            checks_run=list(set(checks_run)),
            paper_title=doc.meta.title
        )
