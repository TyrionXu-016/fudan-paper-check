"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { JobTable } from "@/components/JobTable";
import { Navbar } from "@/components/Navbar";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { JobListItem } from "@/lib/types";

export default function DashboardPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    api
      .listJobs(token)
      .then(setJobs)
      .finally(() => setFetching(false));
  }, [loading, token, router]);

  if (loading || !user) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>;
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)]">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-stone-900">历史任务</h2>
            <p className="mt-1 text-sm text-stone-500">查看你提交过的论文预检查记录。</p>
          </div>
          <Link
            href="/upload"
            className="rounded-full bg-teal-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-800"
          >
            新建检查
          </Link>
        </div>
        {fetching ? (
          <div className="rounded-2xl bg-white p-10 text-center text-stone-500">加载任务列表…</div>
        ) : (
          <JobTable jobs={jobs} />
        )}
      </main>
    </div>
  );
}
