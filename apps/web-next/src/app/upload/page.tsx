"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function UploadPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [mainFile, setMainFile] = useState<File | null>(null);
  const [mineruFile, setMineruFile] = useState<File | null>(null);
  const [journalProfile, setJournalProfile] = useState("scut_natural_science");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !token) router.replace("/login");
  }, [loading, token, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !mainFile) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await api.upload(token, mainFile, journalProfile, mineruFile);
      router.push(`/jobs/${res.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>;
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <h2 className="text-2xl font-semibold text-stone-900">上传论文</h2>
        <p className="mt-1 text-sm text-stone-500">支持 PDF 或 maker.md，可选附带 mineru.md 用于表格融合。</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-5 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
          <label className="block text-sm text-stone-600">
            主文件
            <input
              type="file"
              required
              accept=".pdf,.md,.markdown"
              onChange={(e) => setMainFile(e.target.files?.[0] ?? null)}
              className="mt-2 block w-full rounded-xl border border-dashed border-stone-300 px-4 py-3"
            />
          </label>

          <label className="block text-sm text-stone-600">
            MinerU 文件（可选）
            <input
              type="file"
              accept=".md,.markdown"
              onChange={(e) => setMineruFile(e.target.files?.[0] ?? null)}
              className="mt-2 block w-full rounded-xl border border-dashed border-stone-300 px-4 py-3"
            />
          </label>

          <label className="block text-sm text-stone-600">
            期刊模板
            <select
              value={journalProfile}
              onChange={(e) => setJournalProfile(e.target.value)}
              className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3"
            >
              <option value="fudan_thesis">复旦大学博士、硕士学位论文规范</option>
              <option value="scut_natural_science">华南理工大学学报（自然科学版）</option>
              <option value="generic">通用中文学术论文</option>
            </select>
          </label>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-teal-700 py-3 font-medium text-white disabled:opacity-60"
          >
            {submitting ? "提交中…" : "开始检查"}
          </button>
        </form>
      </main>
    </div>
  );
}
