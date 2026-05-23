import type { Issue } from "@/lib/types";

const SEVERITY_CLASS: Record<string, string> = {
  error: "border-l-red-500",
  warning: "border-l-amber-500",
  info: "border-l-blue-500",
};

export function IssueList({ issues }: { issues: Issue[] }) {
  if (!issues.length) {
    return <div className="rounded-2xl bg-emerald-50 p-6 text-emerald-800">未发现问题。</div>;
  }

  return (
    <div className="space-y-3">
      {issues.map((issue, index) => (
        <article
          key={`${issue.code}-${index}`}
          className={`rounded-xl border border-stone-200 border-l-4 bg-white p-4 ${SEVERITY_CLASS[issue.severity]}`}
        >
          <div className="mb-2 flex items-center justify-between gap-3 text-xs text-stone-500">
            <code className="rounded bg-stone-100 px-2 py-1 text-stone-700">{issue.code}</code>
            <span>
              {issue.category} · {issue.severity}
            </span>
          </div>
          <p className="text-sm leading-6 text-stone-800">{issue.message}</p>
          {issue.suggestion ? (
            <p className="mt-2 text-sm text-stone-500">建议：{issue.suggestion}</p>
          ) : null}
          {issue.evidence ? (
            <p className="mt-1 text-sm text-stone-500">证据：{issue.evidence}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
