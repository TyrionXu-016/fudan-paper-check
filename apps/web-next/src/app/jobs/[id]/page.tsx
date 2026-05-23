"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { IssueList } from "@/components/IssueList";
import { Navbar } from "@/components/Navbar";
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
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>;
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-5xl px-6 py-8">
        <Link href="/dashboard" className="text-sm text-teal-700 hover:underline">
          ← 返回历史任务
        </Link>

        <div className="mt-4 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-stone-900">
                {report?.paper_title || job?.paper_title || job?.filename || "任务详情"}
              </h2>
              <p className="mt-1 text-sm text-stone-500">任务 ID：{jobId}</p>
            </div>
            {job ? (
              <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">
                {STATUS_LABEL[job.status] || job.status}
              </span>
            ) : null}
          </div>

          {job?.error ? <p className="mt-4 text-sm text-red-600">{job.error}</p> : null}

          {report ? (
            <>
              <div className="mt-6 grid gap-3 sm:grid-cols-4">
                <Stat label="错误" value={report.summary.errors} tone="text-red-600" />
                <Stat label="警告" value={report.summary.warnings} tone="text-amber-600" />
                <Stat label="提示" value={report.summary.infos} tone="text-blue-600" />
                <Stat
                  label="融合得分"
                  value={report.parse_quality.fusion_score}
                  tone="text-teal-700"
                />
              </div>

              {report.parse_quality.fusion_warnings.length ? (
                <div className="mt-4 rounded-2xl bg-teal-50 p-4 text-sm text-teal-900">
                  {report.parse_quality.fusion_warnings.map((w) => (
                    <p key={w}>• {w}</p>
                  ))}
                </div>
              ) : null}

              <div className="mt-6 flex gap-3">
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
                  className="rounded-full border border-stone-200 px-4 py-2 text-sm text-stone-700 hover:bg-stone-50"
                >
                  下载 Markdown 报告
                </button>
              </div>

              <div className="mt-8">
                <h3 className="mb-4 text-lg font-semibold text-stone-900">问题列表</h3>
                <IssueList issues={report.issues} />
              </div>
            </>
          ) : (
            <p className="mt-6 text-sm text-stone-500">
              {job?.status === "failed" ? "任务失败，请重新上传。" : "正在处理，请稍候…"}
            </p>
          )}
        </div>
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
  tone: string;
}) {
  return (
    <div className="rounded-2xl bg-stone-50 p-4">
      <p className={`text-2xl font-semibold ${tone}`}>{value}</p>
      <p className="text-sm text-stone-500">{label}</p>
    </div>
  );
}
