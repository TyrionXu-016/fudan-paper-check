"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
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
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-lg px-6 py-8">
        <h2 className="text-2xl font-semibold text-stone-900">创建辅导项目</h2>
        <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl bg-white p-6 ring-1 ring-stone-200/80">
          <label className="block text-sm">
            项目标题
            <input
              className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm">
            {isAdvisor ? "学生邮箱" : "导师邮箱"}
            <input
              type="email"
              className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoNotify}
              onChange={(e) => setAutoNotify(e.target.checked)}
            />
            分析完成后自动通知学生（关闭则需导师预审发布）
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-teal-700 py-2.5 text-white disabled:opacity-50"
          >
            {loading ? "创建中…" : "创建"}
          </button>
        </form>
      </main>
    </div>
  );
}
