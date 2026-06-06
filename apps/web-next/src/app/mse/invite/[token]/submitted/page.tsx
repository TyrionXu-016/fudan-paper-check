"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { AuthShell } from "@/components/ui/AppShell";

function SubmittedInner() {
  const params = useParams();
  const search = useSearchParams();
  const token = params.token as string;
  const round = search.get("round");

  return (
    <AuthShell>
      <div className="auth-panel w-full max-w-md text-center">
        <p className="ui-label">已收到稿件</p>
        <h1 className="display-title mt-2 text-3xl">提交成功</h1>
        <p className="mt-4 text-sm leading-relaxed text-ink-muted">
          {round ? `第 ${round} 轮论文已开始分析。` : "论文已开始分析。"}
          注册或登录后可查看审查报告。
        </p>
        <div className="mt-8 flex flex-col gap-3">
          <Link
            href={`/register?email=&role=student&next=${encodeURIComponent(`/mse/projects`)}`}
            className="btn btn-primary w-full"
          >
            注册账号
          </Link>
          <Link href="/login" className="btn btn-secondary w-full">
            登录
          </Link>
          <Link href={`/mse/invite/${token}`} className="link-back mt-2 inline-block">
            返回邀请页
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}

export default function InviteSubmittedPage() {
  return (
    <Suspense
      fallback={
        <AuthShell>
          <p className="text-ink-muted">加载中…</p>
        </AuthShell>
      }
    >
      <SubmittedInner />
    </Suspense>
  );
}
