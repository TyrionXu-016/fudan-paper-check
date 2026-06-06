"use client";

import { useEffect, useState } from "react";
import { issueFingerprint } from "@/lib/mse";
import type { Issue } from "@/lib/types";

const SEVERITY_ROW: Record<string, string> = {
  error: "issue-row--error",
  warning: "issue-row--warning",
  info: "issue-row--info",
};

type IssueListProps = {
  issues: Issue[];
  showPage?: boolean;
  showRuleRef?: boolean;
  onDismiss?: (issue: Issue, fingerprint: string) => void;
  dismissLoading?: string | null;
};

export function IssueList({
  issues,
  showPage = true,
  showRuleRef = true,
  onDismiss,
  dismissLoading,
}: IssueListProps) {
  if (!issues.length) {
    return (
      <div className="alert alert-info text-center font-medium">未发现问题，本轮格式门禁表现良好。</div>
    );
  }

  return (
    <div className="card-surface overflow-hidden">
      <table className="issue-table">
        <thead>
          <tr>
            <th>级别</th>
            {showPage && <th>页码</th>}
            <th>问题</th>
            {showRuleRef && <th>规范引用</th>}
            <th>修改建议</th>
            {onDismiss && <th />}
          </tr>
        </thead>
        <tbody>
          {issues.map((issue, index) => (
            <IssueRow
              key={`${issue.code}-${issue.id ?? index}`}
              issue={issue}
              showPage={showPage}
              showRuleRef={showRuleRef}
              onDismiss={onDismiss}
              dismissLoading={dismissLoading}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IssueRow({
  issue,
  showPage,
  showRuleRef,
  onDismiss,
  dismissLoading,
}: {
  issue: Issue;
  showPage: boolean;
  showRuleRef: boolean;
  onDismiss?: (issue: Issue, fingerprint: string) => void;
  dismissLoading?: string | null;
}) {
  const [fp, setFp] = useState<string | null>(null);

  useEffect(() => {
    issueFingerprint(issue).then(setFp);
  }, [issue]);

  const hint = issue.revision_hint ?? issue.suggested_text ?? issue.suggestion;
  const pageLabel =
    issue.page_line ?? (issue.page != null ? `第 ${issue.page} 页` : issue.line ? `约第 ${issue.line} 行` : "—");

  return (
    <tr className={SEVERITY_ROW[issue.severity] ?? "issue-row--info"}>
      <td>
        <code className="font-[family-name:var(--font-sans)] text-xs text-ink-muted">{issue.code}</code>
        <span className="badge badge-neutral mt-2 capitalize">{issue.severity}</span>
      </td>
      {showPage && (
        <td className="whitespace-nowrap font-[family-name:var(--font-sans)] text-ink-muted">{pageLabel}</td>
      )}
      <td className="max-w-md">
        <p className="leading-relaxed text-ink">{issue.message}</p>
        {issue.original_text && (
          <p className="mt-2 line-clamp-2 text-xs text-ink-faint">原文：{issue.original_text}</p>
        )}
      </td>
      {showRuleRef && (
        <td className="max-w-[10rem] text-xs text-ink-faint">{issue.rule_ref ?? "—"}</td>
      )}
      <td className="max-w-xs text-ink-muted">{hint ?? "—"}</td>
      {onDismiss && fp && (
        <td>
          <button
            type="button"
            disabled={dismissLoading === fp}
            onClick={() => onDismiss(issue, fp)}
            className="btn btn-secondary text-xs"
          >
            {dismissLoading === fp ? "处理中…" : "忽略"}
          </button>
        </td>
      )}
    </tr>
  );
}
