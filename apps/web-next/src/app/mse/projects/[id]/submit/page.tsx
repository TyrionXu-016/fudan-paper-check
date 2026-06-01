"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.tiff,.webp,.zip";

export default function MseSubmitPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { token } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !file) return;
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

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-lg px-6 py-8">
        <Link href={`/mse/projects/${projectId}`} className="text-sm text-teal-700 hover:underline">
          ← 返回项目
        </Link>
        <h2 className="mt-4 text-2xl font-semibold text-stone-900">提交论文</h2>
        <p className="mt-1 text-sm text-stone-500">
          支持 PDF、图片或 zip（多页图片）。系统将自动解析并分析。
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4 rounded-2xl bg-white p-6 ring-1 ring-stone-200/80">
          <label className="block text-sm">
            论文文件
            <input
              type="file"
              accept={ACCEPT}
              className="mt-2 block w-full text-sm text-stone-600"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              required
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading || !file}
            className="w-full rounded-full bg-teal-700 py-2.5 text-white disabled:opacity-50"
          >
            {loading ? "上传并分析中…" : "提交并开始分析"}
          </button>
        </form>
      </main>
    </div>
  );
}
