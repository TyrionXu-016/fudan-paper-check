"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { MseDashboardResponse, MseDashboardTodo } from "@/lib/types";

function TodoList({ items, emptyText }: { items: MseDashboardTodo[]; emptyText: string }) {
  if (!items.length) {
    return <p className="px-5 py-8 text-sm text-ink-muted">{emptyText}</p>;
  }
  return (
    <ul className="divide-y divide-ink/5">
      {items.map((item) => (
        <li key={`${item.type}-${item.project_id}`}>
          <Link
            href={
              item.round_number
                ? `/mse/projects/${item.project_id}/rounds/${item.round_number}`
                : `/mse/projects/${item.project_id}`
            }
            className="list-row"
          >
            <div>
              <p className="font-medium text-ink">{item.title}</p>
              <p className="mt-0.5 font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                {item.type.replace(/_/g, " ")}
              </p>
            </div>
            {item.urgency === "high" && <span className="badge badge-issues">待处理</span>}
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
    return <LoadingScreen />;
  }

  const isAdvisor = (user.role ?? "advisor") === "advisor";
  const advisor = data?.advisor;
  const student = data?.student;

  return (
    <AppShell width="wide">
      <PageHeader
        eyebrow="MSE · 论文辅导"
        title="工作台"
        description={isAdvisor ? "待办、项目状态与最近动态一览。" : "改稿任务与最新轮次进度。"}
        actions={
          <>
            <Link href="/mse/projects" className="btn btn-secondary">
              全部项目
            </Link>
            <Link href="/mse/projects/new" className="btn btn-primary">
              {isAdvisor ? "创建项目" : "发起辅导"}
            </Link>
          </>
        }
      />

      {fetching ? (
        <div className="card-surface p-12 text-center text-ink-muted">加载仪表盘…</div>
      ) : isAdvisor && advisor ? (
        <div className="space-y-10">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard label="项目总数" value={advisor.stats.total_projects} />
            <StatCard label="进行中" value={advisor.stats.active} />
            <StatCard label="待发布" value={advisor.stats.pending_release} />
            <StatCard label="待终审" value={advisor.stats.awaiting_advisor} />
            <StatCard label="解析失败" value={advisor.stats.parse_failed} />
            <StatCard label="已完成" value={advisor.stats.completed} />
          </div>
          <section>
            <h3 className="display-title mb-4 text-xl">待办</h3>
            <div className="card-surface overflow-hidden">
              <TodoList items={advisor.todos} emptyText="暂无待办事项" />
            </div>
          </section>
          <section>
            <h3 className="display-title mb-4 text-xl">最近动态</h3>
            {advisor.activity.length ? (
              <ul className="card-surface space-y-3 p-5">
                {advisor.activity.map((a, i) => (
                  <li key={i} className="text-sm text-ink-muted">
                    <span className="font-[family-name:var(--font-sans)] text-xs text-ink-faint">
                      {a.at.slice(0, 19)}
                    </span>
                    <span className="mx-2 text-ink-faint">—</span>
                    {a.summary}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-muted">暂无动态</p>
            )}
          </section>
        </div>
      ) : student ? (
        <div className="space-y-10">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="我的项目" value={student.stats.my_projects} />
            <StatCard label="改稿中" value={student.stats.in_revision} />
            <StatCard label="待导师终审" value={student.stats.awaiting_advisor} />
            <StatCard label="已完成" value={student.stats.completed} />
          </div>
          <section>
            <h3 className="display-title mb-4 text-xl">待处理</h3>
            <div className="card-surface overflow-hidden">
              <TodoList items={student.action_required} emptyText="暂无待改稿任务" />
            </div>
          </section>
          <section>
            <h3 className="display-title mb-4 text-xl">最近轮次</h3>
            {student.recent.length ? (
              <ul className="card-surface space-y-3 p-5">
                {student.recent.map((a, i) => (
                  <li key={i}>
                    <Link
                      href={`/mse/projects/${a.project_id}`}
                      className="text-sm text-vermillion hover:underline"
                    >
                      {a.summary}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-muted">暂无记录</p>
            )}
          </section>
        </div>
      ) : (
        <div className="card-surface p-12 text-center text-ink-muted">暂无数据</div>
      )}
    </AppShell>
  );
}
