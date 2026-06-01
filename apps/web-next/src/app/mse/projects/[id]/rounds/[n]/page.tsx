"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { IssueList } from "@/components/IssueList";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { reviewStatusClass, reviewStatusLabel } from "@/lib/mse";
import { useAuth } from "@/lib/auth";
import type { Issue, MseRoundReport } from "@/lib/types";

export default function MseRoundReportPage() {
  const params = useParams();
  const projectId = params.id as string;
  const roundNumber = Number(params.n);
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<MseRoundReport | null>(null);
  const [fetching, setFetching] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    const report = await api.getMseRoundReport(token, projectId, roundNumber);
    setData(report);
  }, [token, projectId, roundNumber]);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    load()
      .catch((e) => setError(e instanceof Error ? e.message : "加载失败"))
      .finally(() => setFetching(false));
  }, [loading, token, router, load]);

  const isAdvisor = (user?.role ?? "advisor") === "advisor";
  const issues = data?.report?.issues ?? [];
  const summary = data?.report?.summary;

  async function handleRelease() {
    if (!token) return;
    setActionLoading("release");
    try {
      const updated = await api.releaseMseRound(token, projectId, roundNumber);
      setData(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "发布失败");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleRetry() {
    if (!token) return;
    setActionLoading("retry");
    try {
      await api.retryMseRound(token, projectId, roundNumber);
      router.push(`/mse/projects/${projectId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "重试失败");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleExport(format: "md" | "pdf") {
    if (!token) return;
    setExporting(format);
    try {
      await api.downloadMseRoundExport(token, projectId, roundNumber, format);
    } catch (e) {
      setError(e instanceof Error ? e.message : "导出失败");
    } finally {
      setExporting(null);
    }
  }

  async function handleDismiss(_issue: Issue, fingerprint: string) {
    if (!token) return;
    setActionLoading(fingerprint);
    try {
      await api.dismissMseIssue(token, projectId, roundNumber, fingerprint);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "忽略失败");
    } finally {
      setActionLoading(null);
    }
  }

  if (fetching) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载报告…</div>;
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center text-stone-500">
        {error || "报告不可用"}
      </div>
    );
  }

  const canRelease = isAdvisor && data.review_status === "pending_release";
  const canRetry =
    data.review_status === "parse_failed" || data.review_status === "analysis_failed";

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Link href={`/mse/projects/${projectId}`} className="text-sm text-teal-700 hover:underline">
          ← 返回项目
        </Link>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-stone-900">第 {roundNumber} 轮审查报告</h2>
            <span
              className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-medium ${reviewStatusClass(data.review_status)}`}
            >
              {reviewStatusLabel(data.review_status)}
            </span>
            {!data.released && (
              <p className="mt-2 text-sm text-violet-700">尚未向学生发布</p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={!!exporting}
              onClick={() => handleExport("md")}
              className="rounded-full border border-stone-300 px-4 py-2 text-sm hover:bg-white disabled:opacity-50"
            >
              {exporting === "md" ? "导出中…" : "导出 Markdown"}
            </button>
            <button
              type="button"
              disabled={!!exporting}
              onClick={() => handleExport("pdf")}
              className="rounded-full border border-stone-300 px-4 py-2 text-sm hover:bg-white disabled:opacity-50"
            >
              {exporting === "pdf" ? "导出中…" : "导出 PDF"}
            </button>
            {canRelease && (
              <button
                type="button"
                disabled={actionLoading === "release"}
                onClick={handleRelease}
                className="rounded-full bg-violet-700 px-5 py-2 text-sm text-white hover:bg-violet-800 disabled:opacity-50"
              >
                {actionLoading === "release" ? "发布中…" : "发布给学生"}
              </button>
            )}
            {canRetry && (
              <button
                type="button"
                disabled={actionLoading === "retry"}
                onClick={handleRetry}
                className="rounded-full border border-stone-300 px-5 py-2 text-sm hover:bg-white disabled:opacity-50"
              >
                重新分析
              </button>
            )}
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {data.gate && (
          <div
            className={`mt-6 rounded-2xl p-4 text-sm ${
              data.gate.passed ? "bg-emerald-50 text-emerald-900" : "bg-amber-50 text-amber-900"
            }`}
          >
            门禁：{data.gate.passed ? "通过" : "未通过"} — {data.gate.reason}
          </div>
        )}

        {summary && (
          <div className="mt-6 grid grid-cols-3 gap-4">
            <Stat label="错误" value={summary.errors} tone="red" />
            <Stat label="警告" value={summary.warnings} tone="amber" />
            <Stat label="提示" value={summary.infos} tone="blue" />
          </div>
        )}

        {data.diff && data.diff.base_round > 0 && (
          <section className="mt-8">
            <h3 className="mb-3 text-lg font-medium text-stone-900">与第 {data.diff.base_round} 轮对比</h3>
            <div className="grid gap-4 sm:grid-cols-3 text-sm">
              <DiffCard label="已修复" count={data.diff.fixed.length} className="text-emerald-700" />
              <DiffCard label="仍存在问题" count={data.diff.persistent.length} className="text-amber-700" />
              <DiffCard label="新增" count={data.diff.new.length} className="text-red-700" />
            </div>
          </section>
        )}

        <section className="mt-8">
          <h3 className="mb-3 text-lg font-medium text-stone-900">问题清单</h3>
          <IssueList
            issues={issues}
            onDismiss={isAdvisor ? handleDismiss : undefined}
            dismissLoading={actionLoading}
          />
        </section>
      </main>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "red" | "amber" | "blue";
}) {
  const bg = { red: "bg-red-50", amber: "bg-amber-50", blue: "bg-blue-50" }[tone];
  return (
    <div className={`rounded-2xl ${bg} p-4 ring-1 ring-stone-200/50`}>
      <p className="text-xs text-stone-500">{label}</p>
      <p className="text-2xl font-semibold text-stone-900">{value}</p>
    </div>
  );
}

function DiffCard({
  label,
  count,
  className,
}: {
  label: string;
  count: number;
  className: string;
}) {
  return (
    <div className="rounded-xl bg-white p-4 ring-1 ring-stone-200/80">
      <p className="text-stone-500">{label}</p>
      <p className={`text-xl font-semibold ${className}`}>{count}</p>
    </div>
  );
}
