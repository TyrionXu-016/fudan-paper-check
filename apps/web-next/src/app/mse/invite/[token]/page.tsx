"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AuthShell } from "@/components/ui/AppShell";
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
    return (
      <AuthShell>
        <p className="auth-panel text-center text-ink-muted">加载邀请…</p>
      </AuthShell>
    );
  }

  if (!info) {
    return (
      <AuthShell>
        <p className="auth-panel text-center text-ink-muted">{error || "邀请不存在"}</p>
      </AuthShell>
    );
  }

  const roleLabel = info.target_role === "student" ? "学生" : "导师";
  const loginNext = `/mse/invite/${token}`;
  const regQs = new URLSearchParams({
    email: info.target_email,
    role: info.target_role,
    next: loginNext,
  });
  const canGuestSubmit = info.target_role === "student" && !info.used && !info.expired;

  return (
    <AuthShell>
      <div className="auth-panel w-full max-w-md">
        <div className="invite-brand">
          <p className="ui-label">论文辅导邀请</p>
          <h1 className="display-title mt-2 text-3xl">{info.project_title}</h1>
        </div>
        <p className="text-sm leading-relaxed text-ink-muted">
          邀请您以<strong className="text-ink">{roleLabel}</strong>身份参与（{info.target_email}）
        </p>

        {info.used && (
          <p className="alert alert-warn mt-6">该邀请已被使用。</p>
        )}
        {info.expired && !info.used && (
          <p className="alert alert-accent mt-6">邀请已过期。</p>
        )}

        {canGuestSubmit && (
          <form
            onSubmit={handleInviteSubmit}
            className="card-inset mt-6 space-y-3 p-4"
          >
            <p className="font-medium text-jade">免登录提交初稿</p>
            <p className="text-xs text-ink-faint">上传后将自动绑定为学生账号（{info.target_email}）。</p>
            <input
              type="file"
              accept={ACCEPT}
              required
              className="input-field"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button
              type="submit"
              disabled={uploading || !file}
              className="btn btn-primary w-full"
            >
              {uploading ? "上传并分析中…" : "直接提交论文"}
            </button>
          </form>
        )}

        {!info.used && !info.expired && (
          <div className="mt-6 space-y-3">
            {!user ? (
              <>
                <p className="text-sm text-ink-muted">或先登录/注册后再加入项目。</p>
                <Link href={`/register?${regQs.toString()}`} className="btn btn-primary block w-full text-center">
                  注册并加入
                </Link>
                <Link
                  href={`/login?next=${encodeURIComponent(loginNext)}`}
                  className="btn btn-secondary block w-full text-center"
                >
                  已有账号，登录
                </Link>
              </>
            ) : (
              <>
                {user.email.toLowerCase() !== info.target_email.toLowerCase() && (
                  <p className="alert alert-warn">
                    当前登录邮箱（{user.email}）与邀请邮箱不一致，请切换账号。
                  </p>
                )}
                {user.role !== info.target_role && (
                  <p className="alert alert-warn">
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
                  className="btn btn-primary w-full"
                >
                  {accepting ? "加入中…" : "接受邀请"}
                </button>
              </>
            )}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-vermillion">{error}</p>}
      </div>
    </AuthShell>
  );
}
