"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { projectStatusLabel } from "@/lib/mse";
import { useAuth } from "@/lib/auth";
import type { MseProject } from "@/lib/types";

export default function MseProjectsPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<MseProject[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    api
      .listMseProjects(token)
      .then(setProjects)
      .finally(() => setFetching(false));
  }, [loading, token, router]);

  const isAdvisor = (user?.role ?? "advisor") === "advisor";

  if (loading || !user) {
    return <LoadingScreen />;
  }

  return (
    <AppShell width="narrow">
      <PageHeader
        eyebrow="项目"
        title="辅导项目"
        description={isAdvisor ? "您作为导师负责的项目列表。" : "您参与的学生项目。"}
        backHref="/mse/dashboard"
        backLabel="工作台"
        actions={
          <Link href="/mse/projects/new" className="btn btn-primary">
            创建项目
          </Link>
        }
      />

      {fetching ? (
        <div className="card-surface p-12 text-center text-ink-muted">加载中…</div>
      ) : !projects.length ? (
        <div className="card-surface p-12 text-center text-ink-muted">
          暂无项目，{" "}
          <Link href="/mse/projects/new" className="text-vermillion hover:underline">
            创建一个
          </Link>
        </div>
      ) : (
        <ul className="card-surface divide-y divide-ink/5 overflow-hidden">
          {projects.map((p) => (
            <li key={p.id}>
              <Link href={`/mse/projects/${p.id}`} className="list-row">
                <div>
                  <p className="font-medium text-ink">{p.title}</p>
                  <p className="mt-1 font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                    {projectStatusLabel(p.status)} · 第 {p.current_round} 轮
                  </p>
                </div>
                <span className="text-vermillion">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
