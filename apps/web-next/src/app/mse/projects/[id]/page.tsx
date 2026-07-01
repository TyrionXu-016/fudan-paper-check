"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
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
  const [ruleFile, setRuleFile] = useState<File | null>(null);
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
    if (!token || !ruleFile) return;
    setRulesLoading(true);
    try {
      const updated = await api.uploadMseRules(token, projectId, ruleFile);
      setProject(updated);
      setRuleFile(null);
    } finally {
      setRulesLoading(false);
    }
  }

  async function handleIndexDefaultRules() {
    if (!token) return;
    setRulesLoading(true);
    try {
      const updated = await api.uploadMseDefaultRules(token, projectId);
      setProject(updated);
    } finally {
      setRulesLoading(false);
    }
  }

  if (fetching || !project) {
    return <LoadingScreen label={fetching ? "加载项目…" : "项目不存在"} />;
  }

  const pendingRelease = rounds.some((r) => r.review_status === "pending_release");
  const awaitingInnovation = project.status === "awaiting_advisor";
  const setupMissingReason =
    !project.advisor_id || !project.student_id
      ? "项目尚缺成员绑定，请生成邀请链接发送给对方。"
      : (project.rule_base_ids?.length ?? 0) === 0
        ? "项目尚未加载论文规范，请先加载默认规范或上传规范文件。"
        : "";
  const canStudentSubmit =
    isStudent &&
    !setupMissingReason &&
    (project.status === "active" || project.status === "analyzing");
  const needsMember =
    project.status === "pending_member" ||
    project.status === "draft" ||
    !project.student_id ||
    !project.advisor_id;

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow={`${projectStatusLabel(project.status)} · 第 ${project.current_round} 轮`}
        title={project.title}
        description={
          <>
            {project.advisor_email && `导师 ${project.advisor_email}`}
            {project.student_email && ` · 学生 ${project.student_email}`}
            {(project.rule_base_ids?.length ?? 0) > 0 && (
              <span className="mt-2 block text-jade">已加载默认规范（含论文常见问题）</span>
            )}
          </>
        }
        backHref="/mse/dashboard"
        backLabel="工作台"
        actions={
          <div className="flex flex-wrap gap-2">
            {canStudentSubmit && (
              <Link href={`/mse/projects/${projectId}/submit`} className="btn btn-primary">
                提交论文
              </Link>
            )}
            {isStudent && !canStudentSubmit && (
              <button type="button" disabled className="btn btn-secondary">
                提交论文
              </button>
            )}
            {project.current_round > 0 && (
              <Link
                href={`/mse/projects/${projectId}/rounds/${project.current_round}`}
                className="btn btn-secondary"
              >
                最新报告
              </Link>
            )}
          </div>
        }
      />

      {isAdvisor && (
        <div className="card-inset mb-6 flex flex-wrap items-center gap-2 p-4">
          <label className="btn btn-secondary cursor-pointer">
            {ruleFile ? ruleFile.name : "选择规范文件"}
            <input
              type="file"
              accept=".md,.docx,.pdf"
              className="hidden"
              onChange={(e) => setRuleFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <button
            type="button"
            onClick={handleUploadRules}
            disabled={rulesLoading || !ruleFile}
            className="btn btn-primary"
          >
            {rulesLoading ? "上传中…" : "上传规范"}
          </button>
          <button
            type="button"
            onClick={handleIndexDefaultRules}
            disabled={rulesLoading}
            className="btn btn-ghost text-xs"
          >
            重新索引默认规范
          </button>
        </div>
      )}

      {needsMember && (
        <div className="alert alert-warn mb-6">
          <p>{setupMissingReason || "项目尚未准备完成，暂不能提交论文。"}</p>
          <button
            type="button"
            onClick={handleSendInvite}
            disabled={inviteLoading}
            className="btn btn-primary mt-3"
          >
            {inviteLoading ? "生成中…" : "生成邀请链接"}
          </button>
          {inviteUrl && (
            <p className="mt-3 break-all font-[family-name:var(--font-sans)] text-xs">
              <Link href={`/mse/invite/${inviteUrl.split("/").pop()}`} className="text-vermillion underline">
                {inviteUrl}
              </Link>
            </p>
          )}
        </div>
      )}

      {isAdvisor && awaitingInnovation && (
        <div className="alert alert-info mb-6">
          格式门禁已通过，请进行{" "}
          <Link href={`/mse/projects/${projectId}/review`} className="font-semibold underline">
            创新性审查
          </Link>
          。
        </div>
      )}

      {isAdvisor && pendingRelease && (
        <div className="alert alert-accent mb-6">
          有待发布的分析结果，请进入对应轮次报告页点击「发布给学生」。
        </div>
      )}

      {!project.auto_notify_student && (
        <p className="mb-6 font-[family-name:var(--font-sans)] text-xs text-ink-faint">
          已关闭自动通知学生，分析完成后需导师预审发布。
        </p>
      )}

      <section>
        <h3 className="display-title mb-5 text-xl">修订轮次</h3>
        <div className="card-surface p-6">
          <RoundTimeline projectId={projectId} rounds={rounds} />
        </div>
      </section>
    </AppShell>
  );
}
