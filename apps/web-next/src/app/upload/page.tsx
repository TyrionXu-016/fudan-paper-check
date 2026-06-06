"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
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
    return <LoadingScreen />;
  }

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow="预检查"
        title="上传论文"
        description="支持 PDF 或 maker.md，可选附带 mineru.md 用于表格融合。"
      />

      <form onSubmit={onSubmit} className="card-surface space-y-5 p-6">
        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          主文件
          <input
            type="file"
            required
            accept=".pdf,.md,.markdown"
            onChange={(e) => setMainFile(e.target.files?.[0] ?? null)}
            className="input-field"
          />
        </label>

        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          MinerU 文件（可选）
          <input
            type="file"
            accept=".md,.markdown"
            onChange={(e) => setMineruFile(e.target.files?.[0] ?? null)}
            className="input-field"
          />
        </label>

        <label className="block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          期刊模板
          <select
            value={journalProfile}
            onChange={(e) => setJournalProfile(e.target.value)}
            className="input-field"
          >
            <option value="scut_natural_science">华南理工大学学报（自然科学版）</option>
            <option value="generic">通用中文学术论文</option>
          </select>
        </label>

        {error ? <p className="text-sm text-vermillion">{error}</p> : null}

        <button type="submit" disabled={submitting} className="btn btn-primary w-full py-3">
          {submitting ? "提交中…" : "开始检查"}
        </button>
      </form>
    </AppShell>
  );
}
