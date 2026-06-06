"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { AuthShell } from "@/components/ui/AppShell";

export default function LoginInner() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/mse/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    router.replace(nextPath);
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
      router.push(nextPath);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "登录失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit} className="auth-panel">
        <p className="ui-label">Fudan Paper Check</p>
        <h1 className="display-title mt-2 text-3xl">登录</h1>
        <p className="mt-2 text-sm leading-relaxed text-ink-muted">
          进入论文辅导工作台，查看多轮审阅与格式门禁结果。
        </p>

        <label className="mt-8 block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          邮箱
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
          />
        </label>

        <label className="mt-4 block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          密码
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
          />
        </label>

        {error ? <p className="mt-4 text-sm text-vermillion">{error}</p> : null}

        <button type="submit" disabled={submitting} className="btn btn-primary mt-8 w-full py-3.5">
          {submitting ? "登录中…" : "进入工作台"}
        </button>

        <p className="mt-6 text-center font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          还没有账号？{" "}
          <Link href="/register" className="text-vermillion hover:underline">
            注册
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
