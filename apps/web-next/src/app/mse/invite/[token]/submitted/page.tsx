"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function SubmittedInner() {
  const params = useParams();
  const search = useSearchParams();
  const token = params.token as string;
  const round = search.get("round");

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)] px-6">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 text-center ring-1 ring-stone-200/80">
        <h1 className="text-2xl font-semibold text-stone-900">提交成功</h1>
        <p className="mt-3 text-sm text-stone-600">
          {round ? `第 ${round} 轮论文已开始分析。` : "论文已开始分析。"}
          注册或登录后可查看审查报告。
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <Link
            href={`/register?email=&role=student&next=${encodeURIComponent(`/mse/projects`)}`}
            className="rounded-full bg-teal-700 py-2.5 text-sm text-white"
          >
            注册账号
          </Link>
          <Link href="/login" className="rounded-full border border-stone-300 py-2.5 text-sm text-stone-700">
            登录
          </Link>
          <Link href={`/mse/invite/${token}`} className="text-xs text-stone-500 hover:underline">
            返回邀请页
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function InviteSubmittedPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-stone-500">加载中…</div>}>
      <SubmittedInner />
    </Suspense>
  );
}
