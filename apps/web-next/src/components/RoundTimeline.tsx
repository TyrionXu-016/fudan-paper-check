"use client";

import Link from "next/link";
import type { MseSubmissionRound } from "@/lib/types";
import { reviewStatusClass, reviewStatusLabel } from "@/lib/mse";

export function RoundTimeline({
  projectId,
  rounds,
}: {
  projectId: string;
  rounds: MseSubmissionRound[];
}) {
  if (!rounds.length) {
    return <p className="text-sm text-ink-muted">尚无提交轮次。</p>;
  }

  const sorted = [...rounds].sort((a, b) => b.round_number - a.round_number);

  return (
    <ol className="timeline-rail space-y-0">
      {sorted.map((round) => (
        <li key={round.id} className="relative pb-10 last:pb-0">
          <span className="timeline-dot" aria-hidden />
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <Link
                href={`/mse/projects/${projectId}/rounds/${round.round_number}`}
                className="display-title text-lg text-vermillion transition-colors hover:text-vermillion-deep"
              >
                第 {round.round_number} 轮
              </Link>
              <p className="mt-1 font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                {round.submitted_at?.slice(0, 19) ?? "—"}
                {round.analyzed_at ? ` · 分析于 ${round.analyzed_at.slice(0, 19)}` : ""}
              </p>
            </div>
            <span className={reviewStatusClass(round.review_status)}>
              {reviewStatusLabel(round.review_status)}
            </span>
          </div>
          <p className="mt-3 text-sm text-ink-muted">
            {round.issue_count} 项问题
            {round.error_count > 0 && (
              <span className="ml-2 text-vermillion">{round.error_count} 错误</span>
            )}
            {round.warning_count > 0 && (
              <span className="ml-2 text-gold">{round.warning_count} 警告</span>
            )}
            {round.gate_passed === true && <span className="ml-2 text-jade">· 门禁通过</span>}
          </p>
        </li>
      ))}
    </ol>
  );
}
