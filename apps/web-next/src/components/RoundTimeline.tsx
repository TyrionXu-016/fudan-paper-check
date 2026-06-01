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
    return <p className="text-sm text-stone-500">尚无提交轮次。</p>;
  }

  const sorted = [...rounds].sort((a, b) => b.round_number - a.round_number);

  return (
    <ol className="relative space-y-0 border-l border-stone-200 pl-6">
      {sorted.map((round) => (
        <li key={round.id} className="relative pb-8 last:pb-0">
          <span className="absolute -left-[9px] top-1 h-4 w-4 rounded-full border-2 border-white bg-teal-600 ring-1 ring-teal-600" />
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <Link
                href={`/mse/projects/${projectId}/rounds/${round.round_number}`}
                className="font-medium text-teal-800 hover:underline"
              >
                第 {round.round_number} 轮
              </Link>
              <p className="mt-0.5 text-xs text-stone-500">
                {round.submitted_at?.slice(0, 19) ?? "—"}
                {round.analyzed_at ? ` · 分析于 ${round.analyzed_at.slice(0, 19)}` : ""}
              </p>
            </div>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${reviewStatusClass(round.review_status)}`}
            >
              {reviewStatusLabel(round.review_status)}
            </span>
          </div>
          <p className="mt-2 text-sm text-stone-600">
            {round.issue_count} 项问题
            {round.error_count > 0 && (
              <span className="ml-2 text-red-600">{round.error_count} 错误</span>
            )}
            {round.warning_count > 0 && (
              <span className="ml-2 text-amber-600">{round.warning_count} 警告</span>
            )}
            {round.gate_passed === true && (
              <span className="ml-2 text-emerald-600">· 门禁通过</span>
            )}
          </p>
        </li>
      ))}
    </ol>
  );
}
