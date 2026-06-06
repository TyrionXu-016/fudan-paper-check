"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function NewMseProjectPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const isAdvisor = (user?.role ?? "advisor") === "advisor";
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [autoNotify, setAutoNotify] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const body = isAdvisor
        ? { title, student_email: email, auto_notify_student: autoNotify }
        : { title, advisor_email: email, auto_notify_student: autoNotify };
      const project = await api.createMseProject(token, body);
      router.push(`/mse/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow="新建"
        title="创建辅导项目"
        description="绑定导师与学生邮箱，系统将自动索引默认规范（含论文常见问题）。"
        backHref="/mse/projects"
        backLabel="项目列表"
      />

      <form onSubmit={submit} className="card-surface space-y-5 p-6">
        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          项目标题
          <input
            className="input-field"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </label>
        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          {isAdvisor ? "学生邮箱" : "导师邮箱"}
          <input
            type="email"
            className="input-field"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="flex items-start gap-3 font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          <input
            type="checkbox"
            className="mt-1"
            checked={autoNotify}
            onChange={(e) => setAutoNotify(e.target.checked)}
          />
          <span>分析完成后自动通知学生（关闭则需导师预审发布）</span>
        </label>
        {error && <p className="text-sm text-vermillion">{error}</p>}
        <button type="submit" disabled={loading} className="btn btn-primary w-full py-3">
          {loading ? "创建中…" : "创建项目"}
        </button>
      </form>
    </AppShell>
  );
}
