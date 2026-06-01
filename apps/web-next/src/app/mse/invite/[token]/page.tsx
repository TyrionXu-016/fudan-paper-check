"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { InviteInfo } from "@/lib/types";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.tiff,.webp,.zip";

export default function MseInvitePage() {
  const params = useParams();
  const token = params.token as string;
  const { user, token: authToken } = useAuth();
  const router = useRouter();
  const [info, setInfo] = useState<InviteInfo | null>(null);
  const [fetching, setFetching] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getInviteInfo(token)
      .then(setInfo)
      .catch((e) => setError(e instanceof Error ? e.message : "邀请无效"))
      .finally(() => setFetching(false));
  }, [token]);

  async function handleAccept() {
    if (!authToken) return;
    setAccepting(true);
    setError("");
    try {
      const project = await api.acceptInvite(authToken, token);
      router.push(`/mse/projects/${project.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "接受失败");
    } finally {
      setAccepting(false);
    }
  }

  async function handleInviteSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const res = await api.submitMsePaperViaInvite(token, file);
      router.push(`/mse/invite/${token}/submitted?round=${res.round_number}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setUploading(false);
    }
  }

  if (fetching) {
    return <div className="flex min-h-screen items-center justify-center text-stone-500">加载邀请…</div>;
  }

  if (!info) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 text-stone-600">
        {error || "邀请不存在"}
      </div>
    );
  }

  const roleLabel = info.target_role === "student" ? "学生" : "导师";
  const loginNext = `/mse/invite/${token}`;
  const regQs = new URLSearchParams({
    email: info.target_email,
    role: info.target_role,
    next: loginNext,
  });
  const canGuestSubmit =
    info.target_role === "student" && !info.used && !info.expired;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,#faf7f0,#f4f1ea)] px-6 py-10">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 ring-1 ring-stone-200/80">
        <h1 className="text-2xl font-semibold text-stone-900">加入辅导项目</h1>
        <p className="mt-2 text-lg text-stone-800">{info.project_title}</p>
        <p className="mt-4 text-sm text-stone-600">
          邀请您以<strong>{roleLabel}</strong>身份参与（{info.target_email}）
        </p>

        {info.used && (
          <p className="mt-4 rounded-xl bg-stone-100 p-4 text-sm text-stone-600">该邀请已被使用。</p>
        )}
        {info.expired && !info.used && (
          <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">邀请已过期。</p>
        )}

        {canGuestSubmit && (
          <form onSubmit={handleInviteSubmit} className="mt-6 space-y-3 rounded-2xl border border-teal-100 bg-teal-50/50 p-4">
            <p className="text-sm font-medium text-teal-900">免登录提交初稿</p>
            <p className="text-xs text-stone-600">上传后将自动绑定为学生账号（{info.target_email}）。</p>
            <input
              type="file"
              accept={ACCEPT}
              required
              className="block w-full text-sm text-stone-600"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button
              type="submit"
              disabled={uploading || !file}
              className="w-full rounded-full bg-teal-700 py-2.5 text-sm text-white disabled:opacity-50"
            >
              {uploading ? "上传并分析中…" : "直接提交论文"}
            </button>
          </form>
        )}

        {!info.used && !info.expired && (
          <div className="mt-6 space-y-3">
            {!user ? (
              <>
                <p className="text-sm text-stone-500">或先登录/注册后再加入项目。</p>
                <Link
                  href={`/register?${regQs.toString()}`}
                  className="block w-full rounded-full bg-stone-800 py-2.5 text-center text-sm text-white"
                >
                  注册并加入
                </Link>
                <Link
                  href={`/login?next=${encodeURIComponent(loginNext)}`}
                  className="block w-full rounded-full border border-stone-300 py-2.5 text-center text-sm text-stone-700"
                >
                  已有账号，登录
                </Link>
              </>
            ) : (
              <>
                {user.email.toLowerCase() !== info.target_email.toLowerCase() && (
                  <p className="text-sm text-amber-700">
                    当前登录邮箱（{user.email}）与邀请邮箱不一致，请切换账号。
                  </p>
                )}
                {user.role !== info.target_role && (
                  <p className="text-sm text-amber-700">
                    当前账号角色为 {user.role}，邀请要求 {info.target_role}。
                  </p>
                )}
                <button
                  type="button"
                  disabled={
                    accepting ||
                    user.email.toLowerCase() !== info.target_email.toLowerCase() ||
                    user.role !== info.target_role
                  }
                  onClick={handleAccept}
                  className="w-full rounded-full bg-teal-700 py-2.5 text-sm text-white disabled:opacity-50"
                >
                  {accepting ? "加入中…" : "接受邀请"}
                </button>
              </>
            )}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}
