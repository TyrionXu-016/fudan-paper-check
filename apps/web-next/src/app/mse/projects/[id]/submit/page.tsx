"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { projectStatusLabel } from "@/lib/mse";
import type { MseProject } from "@/lib/types";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.tiff,.webp,.zip";

export default function MseSubmitPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [project, setProject] = useState<MseProject | null>(null);
  const [projectLoading, setProjectLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!token) router.replace("/login");
  }, [authLoading, token, router]);

  useEffect(() => {
    if (authLoading || !token) return;
    let active = true;
    api
      .getMseProject(token, projectId)
      .then((nextProject) => {
        if (active) setProject(nextProject);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "项目加载失败");
      })
      .finally(() => {
        if (active) setProjectLoading(false);
      });
    return () => {
      active = false;
    };
  }, [authLoading, token, projectId]);

  const submitBlockReason = (() => {
    if (!project) return "项目加载失败，暂不能提交论文。";
    if (project.status !== "active" && project.status !== "analyzing") {
      if (project.status === "pending_member") return "项目成员尚未绑定完成，请先通过邀请链接完成加入。";
      if (project.status === "draft") return "项目尚未准备完成，请先绑定导师和学生，并加载论文规范。";
      return `当前项目状态为「${projectStatusLabel(project.status)}」，暂不能提交论文。`;
    }
    if (!project.advisor_id || !project.student_id) return "项目需要同时绑定导师和学生后才能提交论文。";
    if ((project.rule_base_ids?.length ?? 0) === 0) return "项目需要先加载论文规范后才能提交论文。";
    return "";
  })();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !file || submitBlockReason) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.submitMsePaper(token, projectId, file);
      router.push(`/mse/projects/${projectId}/rounds/${res.round_number}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  if (authLoading || projectLoading || !user) {
    return <LoadingScreen />;
  }

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow="提交"
        title="上传论文"
        description="支持 PDF、图片或 zip（多页图片）。提交后将自动解析并进入审阅流程。"
        backHref={`/mse/projects/${projectId}`}
        backLabel="项目"
      />

      <form onSubmit={submit} className="card-surface space-y-5 p-6">
        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          论文文件
          <input
            type="file"
            accept={ACCEPT}
            className="input-field file:mr-4 file:rounded-full file:border-0 file:bg-paper-deep file:px-4 file:py-2 file:text-sm file:text-ink"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </label>
        {submitBlockReason ? (
          <p className="rounded-md bg-vermillion/10 p-3 text-sm leading-relaxed text-vermillion">
            {submitBlockReason}
          </p>
        ) : null}
        {error && <p className="text-sm text-vermillion">{error}</p>}
        <button
          type="submit"
          disabled={loading || !file || Boolean(submitBlockReason)}
          className="btn btn-primary w-full py-3"
        >
          {loading ? "上传并分析中…" : "提交并开始分析"}
        </button>
      </form>
    </AppShell>
  );
}
