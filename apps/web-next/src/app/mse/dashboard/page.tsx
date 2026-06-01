"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { MseDashboardResponse, MseDashboardTodo } from "@/lib/types";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-stone-200/80">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-stone-900">{value}</p>
    </div>
  );
}

function TodoList({ items, emptyText }: { items: MseDashboardTodo[]; emptyText: string }) {
  if (!items.length) {
    return <p className="text-sm text-stone-500">{emptyText}</p>;
  }
  return (
    <ul className="divide-y divide-stone-100 rounded-2xl bg-white ring-1 ring-stone-200/80">
      {items.map((item) => (
        <li key={`${item.type}-${item.project_id}`}>
          <Link
            href={
              item.round_number
                ? `/mse/projects/${item.project_id}/rounds/${item.round_number}`
                : `/mse/projects/${item.project_id}`
            }
            className="flex items-center justify-between px-5 py-4 hover:bg-stone-50"
          >
            <div>
              <p className="font-medium text-stone-900">{item.title}</p>
              <p className="text-xs text-stone-500">{item.type.replace(/_/g, " ")}</p>
            </div>
            {item.urgency === "high" && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">待处理</span>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function MseDashboardPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<MseDashboardResponse | null>(null);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    api
      .mseDashboard(token)
      .then(setData)
      .finally(() => setFetching(false));
  }, [loading, token, router]);

  if (loading || !user) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>;
  }

  const isAdvisor = (user.role ?? "advisor") === "advisor";
  const advisor = data?.advisor;
  const student = data?.student;

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-stone-900">论文辅导仪表盘</h2>
            <p className="mt-1 text-sm text-stone-500">
              {isAdvisor ? "查看待办项目与最近动态。" : "查看改稿任务与最新轮次。"}
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/mse/projects"
              className="rounded-full border border-stone-300 px-5 py-2.5 text-sm font-medium text-stone-700 hover:bg-white"
            >
              全部项目
            </Link>
            {isAdvisor && (
              <Link
                href="/mse/projects/new"
                className="rounded-full bg-teal-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-800"
              >
                创建项目
              </Link>
            )}
            {!isAdvisor && (
              <Link
                href="/mse/projects/new"
                className="rounded-full bg-teal-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-800"
              >
                发起辅导
              </Link>
            )}
          </div>
        </div>

        {fetching ? (
          <div className="rounded-2xl bg-white p-10 text-center text-stone-500">加载仪表盘…</div>
        ) : isAdvisor && advisor ? (
          <div className="space-y-8">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <StatCard label="项目总数" value={advisor.stats.total_projects} />
              <StatCard label="进行中" value={advisor.stats.active} />
              <StatCard label="待发布" value={advisor.stats.pending_release} />
              <StatCard label="待终审" value={advisor.stats.awaiting_advisor} />
              <StatCard label="解析失败" value={advisor.stats.parse_failed} />
              <StatCard label="已完成" value={advisor.stats.completed} />
            </div>
            <section>
              <h3 className="mb-3 text-lg font-medium text-stone-900">待办</h3>
              <TodoList items={advisor.todos} emptyText="暂无待办事项" />
            </section>
            <section>
              <h3 className="mb-3 text-lg font-medium text-stone-900">最近动态</h3>
              {advisor.activity.length ? (
                <ul className="space-y-2 rounded-2xl bg-white p-5 ring-1 ring-stone-200/80">
                  {advisor.activity.map((a, i) => (
                    <li key={i} className="text-sm text-stone-600">
                      <span className="text-stone-400">{a.at.slice(0, 19)}</span> — {a.summary}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-stone-500">暂无动态</p>
              )}
            </section>
          </div>
        ) : student ? (
          <div className="space-y-8">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="我的项目" value={student.stats.my_projects} />
              <StatCard label="改稿中" value={student.stats.in_revision} />
              <StatCard label="待导师终审" value={student.stats.awaiting_advisor} />
              <StatCard label="已完成" value={student.stats.completed} />
            </div>
            <section>
              <h3 className="mb-3 text-lg font-medium text-stone-900">待处理</h3>
              <TodoList items={student.action_required} emptyText="暂无待改稿任务" />
            </section>
            <section>
              <h3 className="mb-3 text-lg font-medium text-stone-900">最近轮次</h3>
              {student.recent.length ? (
                <ul className="space-y-2 rounded-2xl bg-white p-5 ring-1 ring-stone-200/80">
                  {student.recent.map((a, i) => (
                    <li key={i}>
                      <Link href={`/mse/projects/${a.project_id}`} className="text-sm text-teal-800 hover:underline">
                        {a.summary}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-stone-500">暂无记录</p>
              )}
            </section>
          </div>
        ) : (
          <div className="rounded-2xl bg-white p-10 text-center text-stone-500">暂无数据</div>
        )}
      </main>
    </div>
  );
}
