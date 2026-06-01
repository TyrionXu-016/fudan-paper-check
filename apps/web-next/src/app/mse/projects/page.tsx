"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
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

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-stone-900">辅导项目</h2>
            <p className="mt-1 text-sm text-stone-500">
              {isAdvisor ? "您作为导师的项目" : "您参与的学生项目"}
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/mse/dashboard" className="text-sm text-teal-700 hover:underline">
              仪表盘
            </Link>
            <Link
              href="/mse/projects/new"
              className="rounded-full bg-teal-700 px-4 py-2 text-sm text-white hover:bg-teal-800"
            >
              创建项目
            </Link>
          </div>
        </div>

        {fetching ? (
          <div className="rounded-2xl bg-white p-10 text-center text-stone-500">加载中…</div>
        ) : !projects.length ? (
          <div className="rounded-2xl bg-white p-10 text-center text-stone-500">
            暂无项目，{" "}
            <Link href="/mse/projects/new" className="text-teal-700 hover:underline">
              创建一个
            </Link>
          </div>
        ) : (
          <ul className="divide-y divide-stone-100 rounded-2xl bg-white ring-1 ring-stone-200/80">
            {projects.map((p) => (
              <li key={p.id}>
                <Link
                  href={`/mse/projects/${p.id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-stone-50"
                >
                  <div>
                    <p className="font-medium text-stone-900">{p.title}</p>
                    <p className="text-xs text-stone-500">
                      {projectStatusLabel(p.status)} · 第 {p.current_round} 轮
                    </p>
                  </div>
                  <span className="text-xs text-stone-400">→</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
