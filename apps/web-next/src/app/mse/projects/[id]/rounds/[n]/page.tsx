"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { IssueList } from "@/components/IssueList";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
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
    return <LoadingScreen label="加载报告…" />;
  }

  if (!data) {
    return <LoadingScreen label={error || "报告不可用"} />;
  }

  const canRelease = isAdvisor && data.review_status === "pending_release";
  const canRetry =
    data.review_status === "parse_failed" || data.review_status === "analysis_failed";

  return (
    <AppShell width="wide">
      <PageHeader
        eyebrow="审查报告"
        title={`第 ${roundNumber} 轮`}
        description={
          <>
            <span className={`${reviewStatusClass(data.review_status)} mr-2`}>
              {reviewStatusLabel(data.review_status)}
            </span>
            {!data.released && (
              <span className="text-ink-muted">尚未向学生发布</span>
            )}
          </>
        }
        backHref={`/mse/projects/${projectId}`}
        backLabel="项目"
        actions={
          <>
            <button
              type="button"
              disabled={!!exporting}
              onClick={() => handleExport("md")}
              className="btn btn-secondary"
            >
              {exporting === "md" ? "导出中…" : "Markdown"}
            </button>
            <button
              type="button"
              disabled={!!exporting}
              onClick={() => handleExport("pdf")}
              className="btn btn-secondary"
            >
              {exporting === "pdf" ? "导出中…" : "PDF"}
            </button>
            {canRelease && (
              <button
                type="button"
                disabled={actionLoading === "release"}
                onClick={handleRelease}
                className="btn btn-primary"
              >
                {actionLoading === "release" ? "发布中…" : "发布给学生"}
              </button>
            )}
            {canRetry && (
              <button
                type="button"
                disabled={actionLoading === "retry"}
                onClick={handleRetry}
                className="btn btn-secondary"
              >
                重新分析
              </button>
            )}
          </>
        }
      />

      {error && <p className="mb-4 text-sm text-vermillion">{error}</p>}

      {data.gate && (
        <div className={`alert mb-6 ${data.gate.passed ? "alert-info" : "alert-warn"}`}>
          门禁：{data.gate.passed ? "通过" : "未通过"} — {data.gate.reason}
        </div>
      )}

      {summary && (
        <div className="mb-8 grid grid-cols-3 gap-4">
          <Stat label="错误" value={summary.errors} tone="vermillion" />
          <Stat label="警告" value={summary.warnings} tone="gold" />
          <Stat label="提示" value={summary.infos} tone="jade" />
        </div>
      )}

      {data.diff && data.diff.base_round > 0 && (
        <section className="mb-8">
          <h3 className="display-title mb-4 text-xl">与第 {data.diff.base_round} 轮对比</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            <DiffCard label="已修复" count={data.diff.fixed.length} className="text-jade" />
            <DiffCard label="仍存在问题" count={data.diff.persistent.length} className="text-gold" />
            <DiffCard label="新增" count={data.diff.new.length} className="text-vermillion" />
          </div>
        </section>
      )}

      <section>
        <h3 className="display-title mb-4 text-xl">问题清单</h3>
        <IssueList
          issues={issues}
          onDismiss={isAdvisor ? handleDismiss : undefined}
          dismissLoading={actionLoading}
        />
      </section>
    </AppShell>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "vermillion" | "gold" | "jade";
}) {
  const border =
    tone === "vermillion"
      ? "border-vermillion/20"
      : tone === "gold"
        ? "border-gold/30"
        : "border-jade/25";
  return (
    <div className={`card-surface border-l-4 ${border} p-4`}>
      <p className="font-[family-name:var(--font-sans)] text-xs uppercase tracking-wider text-ink-faint">
        {label}
      </p>
      <p className="stat-value mt-2">{value}</p>
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
    <div className="card-inset p-4">
      <p className="font-[family-name:var(--font-sans)] text-xs text-ink-faint">{label}</p>
      <p className={`stat-value mt-1 text-2xl ${className}`}>{count}</p>
    </div>
  );
}
