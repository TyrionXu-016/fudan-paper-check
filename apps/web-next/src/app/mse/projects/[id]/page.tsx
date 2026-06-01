"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { RoundTimeline } from "@/components/RoundTimeline";
import { api } from "@/lib/api";
import { projectStatusLabel } from "@/lib/mse";
import { useAuth } from "@/lib/auth";
import type { MseProject, MseSubmissionRound } from "@/lib/types";

export default function MseProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [project, setProject] = useState<MseProject | null>(null);
  const [rounds, setRounds] = useState<MseSubmissionRound[]>([]);
  const [fetching, setFetching] = useState(true);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteUrl, setInviteUrl] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    const [p, r] = await Promise.all([
      api.getMseProject(token, projectId),
      api.listMseRounds(token, projectId),
    ]);
    setProject(p);
    setRounds(r);
  }, [token, projectId]);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    load().finally(() => setFetching(false));
  }, [loading, token, router, load]);

  const isAdvisor = (user?.role ?? "advisor") === "advisor";
  const isStudent = !isAdvisor;

  async function handleSendInvite() {
    if (!token) return;
    setInviteLoading(true);
    setInviteUrl("");
    try {
      const res = await api.inviteMember(token, projectId);
      setInviteUrl(res.invite_url);
    } finally {
      setInviteLoading(false);
    }
  }

  async function handleUploadRules() {
    if (!token) return;
    setRulesLoading(true);
    try {
      const updated = await api.uploadMseRules(token, projectId);
      setProject(updated);
    } finally {
      setRulesLoading(false);
    }
  }

  if (fetching || !project) {
    return (
      <div className="flex min-h-screen items-center justify-center text-stone-500">
        {fetching ? "加载项目…" : "项目不存在"}
      </div>
    );
  }

  const pendingRelease = rounds.some((r) => r.review_status === "pending_release");
  const awaitingInnovation = project.status === "awaiting_advisor";
  const needsMember =
    project.status === "pending_member" ||
    project.status === "draft" ||
    !project.student_id ||
    !project.advisor_id;

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <Link href="/mse/dashboard" className="text-sm text-teal-700 hover:underline">
          ← 返回仪表盘
        </Link>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-stone-900">{project.title}</h2>
            <p className="mt-1 text-sm text-stone-500">
              {projectStatusLabel(project.status)} · 当前第 {project.current_round} 轮
            </p>
            <p className="mt-1 text-xs text-stone-400">
              {project.advisor_email && `导师：${project.advisor_email}`}
              {project.student_email && ` · 学生：${project.student_email}`}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {isStudent && (
              <Link
                href={`/mse/projects/${projectId}/submit`}
                className="rounded-full bg-teal-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-800"
              >
                提交论文
              </Link>
            )}
            {isAdvisor && (
              <button
                type="button"
                onClick={handleUploadRules}
                disabled={rulesLoading}
                className="rounded-full border border-stone-300 px-5 py-2.5 text-sm text-stone-700 hover:bg-white disabled:opacity-50"
              >
                {rulesLoading ? "索引中…" : "绑定默认规范"}
              </button>
            )}
            {project.current_round > 0 && (
              <Link
                href={`/mse/projects/${projectId}/rounds/${project.current_round}`}
                className="rounded-full border border-teal-700 px-5 py-2.5 text-sm text-teal-800 hover:bg-teal-50"
              >
                最新报告
              </Link>
            )}
          </div>
        </div>

        {needsMember && (
          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p>项目尚缺成员绑定，请生成邀请链接发送给对方。</p>
            <button
              type="button"
              onClick={handleSendInvite}
              disabled={inviteLoading}
              className="mt-3 rounded-full bg-amber-800 px-4 py-2 text-xs text-white disabled:opacity-50"
            >
              {inviteLoading ? "生成中…" : "生成邀请链接"}
            </button>
            {inviteUrl && (
              <p className="mt-2 break-all text-xs text-stone-700">
                <Link href={`/mse/invite/${inviteUrl.split("/").pop()}`} className="text-teal-800 underline">
                  {inviteUrl}
                </Link>
              </p>
            )}
          </div>
        )}

        {isAdvisor && awaitingInnovation && (
          <div className="mt-6 rounded-2xl border border-teal-200 bg-teal-50 p-4 text-sm text-teal-900">
            格式门禁已通过，请进行{" "}
            <Link href={`/mse/projects/${projectId}/review`} className="font-medium underline">
              创新性审查
            </Link>
            。
          </div>
        )}

        {isAdvisor && pendingRelease && (
          <div className="mt-6 rounded-2xl border border-violet-200 bg-violet-50 p-4 text-sm text-violet-900">
            有待发布的分析结果，请进入对应轮次报告页点击「发布给学生」。
          </div>
        )}

        {!project.auto_notify_student && (
          <p className="mt-4 text-xs text-stone-500">
            本项目已关闭自动通知学生，分析完成后需导师预审发布。
          </p>
        )}

        <section className="mt-8">
          <h3 className="mb-4 text-lg font-medium text-stone-900">修订轮次</h3>
          <div className="rounded-2xl bg-white p-6 ring-1 ring-stone-200/80">
            <RoundTimeline projectId={projectId} rounds={rounds} />
          </div>
        </section>
      </main>
    </div>
  );
}
