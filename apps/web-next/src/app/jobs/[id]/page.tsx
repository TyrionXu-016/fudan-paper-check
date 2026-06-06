"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { IssueList } from "@/components/IssueList";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CheckReport, JobListItem } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  queued: "排队中",
  converting: "PDF 转换中",
  parsing: "文档解析中",
  checking: "执行检查",
  done: "已完成",
  failed: "失败",
};

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const { token, loading, user } = useAuth();
  const router = useRouter();
  const [job, setJob] = useState<(JobListItem & { error?: string }) | null>(null);
  const [report, setReport] = useState<CheckReport | null>(null);

  useEffect(() => {
    if (!loading && !token) router.replace("/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (!token || !jobId) return;

    let active = true;
    const poll = async () => {
      try {
        const nextJob = await api.getJob(token, jobId);
        if (!active) return;
        setJob(nextJob);
        if (nextJob.status === "done") {
          const nextReport = await api.getReport(token, jobId);
          if (active) setReport(nextReport);
          return;
        }
        if (nextJob.status === "failed") return;
        setTimeout(poll, 1500);
      } catch {
        if (active) setTimeout(poll, 2000);
      }
    };

    poll();
    return () => {
      active = false;
    };
  }, [token, jobId]);

  if (loading || !user) {
    return <LoadingScreen />;
  }

  return (
    <AppShell width="wide">
      <PageHeader
        eyebrow="任务详情"
        title={report?.paper_title || job?.paper_title || job?.filename || "预检查"}
        description={`任务 ID：${jobId}`}
        backHref="/dashboard"
        backLabel="历史任务"
        actions={
          job ? (
            <span className="badge badge-neutral">{STATUS_LABEL[job.status] || job.status}</span>
          ) : null
        }
      />

      <div className="card-surface p-6">
        {job?.error ? <p className="text-sm text-vermillion">{job.error}</p> : null}

        {report ? (
          <>
            <div className="mt-2 grid gap-3 sm:grid-cols-4">
              <JobStat label="错误" value={report.summary.errors} className="text-vermillion" />
              <JobStat label="警告" value={report.summary.warnings} className="text-gold" />
              <JobStat label="提示" value={report.summary.infos} className="text-jade" />
              <JobStat
                label="融合得分"
                value={report.parse_quality.fusion_score}
                className="text-ink"
              />
            </div>

            {report.parse_quality.fusion_warnings.length ? (
              <div className="alert alert-info mt-4">
                {report.parse_quality.fusion_warnings.map((w) => (
                  <p key={w}>• {w}</p>
                ))}
              </div>
            ) : null}

            <div className="mt-6">
              <button
                type="button"
                onClick={async () => {
                  if (!token) return;
                  const res = await fetch(api.reportMarkdownUrl(jobId), {
                    headers: { Authorization: `Bearer ${token}` },
                  });
                  const text = await res.text();
                  const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${jobId}.report.md`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="btn btn-secondary"
              >
                下载 Markdown 报告
              </button>
            </div>

            <div className="mt-8">
              <h3 className="display-title mb-4 text-xl">问题列表</h3>
              <IssueList issues={report.issues} />
            </div>
          </>
        ) : (
          <p className="mt-4 text-sm text-ink-muted">
            {job?.status === "failed" ? "任务失败，请重新上传。" : "正在处理，请稍候…"}
          </p>
        )}
      </div>
    </AppShell>
  );
}

function JobStat({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className: string;
}) {
  return (
    <div className="card-inset p-4">
      <p className={`stat-value text-2xl ${className}`}>{value}</p>
      <p className="mt-1 font-[family-name:var(--font-sans)] text-xs text-ink-faint">{label}</p>
    </div>
  );
}
