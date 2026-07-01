"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.tiff,.webp,.zip";

export default function MseSubmitPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!token) router.replace("/login");
  }, [authLoading, token, router]);

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

  if (authLoading || !user) {
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
        {error && <p className="text-sm text-vermillion">{error}</p>}
        <button type="submit" disabled={loading || !file} className="btn btn-primary w-full py-3">
          {loading ? "上传并分析中…" : "提交并开始分析"}
        </button>
      </form>
    </AppShell>
  );
}
