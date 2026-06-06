"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { JobTable } from "@/components/JobTable";
import { AppShell, LoadingScreen } from "@/components/ui/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
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
    return <LoadingScreen />;
  }

  return (
    <AppShell width="wide">
      <PageHeader
        eyebrow="预检查"
        title="历史任务"
        description="查看你提交过的论文预检查记录。"
        actions={
          <Link href="/upload" className="btn btn-primary">
            新建检查
          </Link>
        }
      />
      {fetching ? (
        <div className="card-surface p-12 text-center text-ink-muted">加载任务列表…</div>
      ) : (
        <JobTable jobs={jobs} />
      )}
    </AppShell>
  );
}
