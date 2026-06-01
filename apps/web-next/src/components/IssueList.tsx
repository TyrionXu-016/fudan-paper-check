"use client";

import { useEffect, useState } from "react";
import { issueFingerprint } from "@/lib/mse";
import type { Issue } from "@/lib/types";

const SEVERITY_CLASS: Record<string, string> = {
  error: "border-l-red-500",
  warning: "border-l-amber-500",
  info: "border-l-blue-500",
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
    return <div className="rounded-2xl bg-emerald-50 p-6 text-emerald-800">未发现问题。</div>;
  }

  return (
    <div className="overflow-x-auto rounded-2xl bg-white ring-1 ring-stone-200/80">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-stone-100 bg-stone-50 text-left text-xs text-stone-500">
            <th className="px-4 py-3 font-medium">级别</th>
            {showPage && <th className="px-4 py-3 font-medium">页码</th>}
            <th className="px-4 py-3 font-medium">问题</th>
            {showRuleRef && <th className="px-4 py-3 font-medium">规范引用</th>}
            <th className="px-4 py-3 font-medium">修改建议</th>
            {onDismiss && <th className="px-4 py-3 font-medium" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
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
    <tr className={`border-l-4 ${SEVERITY_CLASS[issue.severity] ?? "border-l-stone-300"}`}>
      <td className="px-4 py-3 align-top">
        <code className="block text-xs text-stone-600">{issue.code}</code>
        <span className="mt-1 inline-block rounded bg-stone-100 px-1.5 py-0.5 text-xs capitalize">
          {issue.severity}
        </span>
      </td>
      {showPage && <td className="whitespace-nowrap px-4 py-3 align-top text-stone-700">{pageLabel}</td>}
      <td className="max-w-md px-4 py-3 align-top">
        <p className="leading-6 text-stone-800">{issue.message}</p>
        {issue.original_text && (
          <p className="mt-1 line-clamp-2 text-xs text-stone-500">原文：{issue.original_text}</p>
        )}
      </td>
      {showRuleRef && (
        <td className="max-w-[10rem] px-4 py-3 align-top text-xs text-stone-500">
          {issue.rule_ref ?? "—"}
        </td>
      )}
      <td className="max-w-xs px-4 py-3 align-top text-stone-600">{hint ?? "—"}</td>
      {onDismiss && fp && (
        <td className="px-4 py-3 align-top">
          <button
            type="button"
            disabled={dismissLoading === fp}
            onClick={() => onDismiss(issue, fp)}
            className="rounded-lg border border-stone-300 px-3 py-1 text-xs text-stone-600 hover:bg-stone-50 disabled:opacity-50"
          >
            {dismissLoading === fp ? "处理中…" : "忽略"}
          </button>
        </td>
      )}
    </tr>
  );
}
