"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    router.replace("/dashboard");
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "登录失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_#ccfbf1,_transparent_35%),linear-gradient(180deg,#faf7f0,#f4f1ea)] px-6">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl border border-stone-200 bg-white p-8 shadow-xl">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">Fudan Paper Check</p>
        <h1 className="mt-2 text-2xl font-semibold text-stone-900">登录</h1>
        <p className="mt-2 text-sm text-stone-500">登录后查看历史任务并上传论文预检查。</p>

        <label className="mt-6 block text-sm text-stone-600">
          邮箱
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3"
          />
        </label>

        <label className="mt-4 block text-sm text-stone-600">
          密码
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3"
          />
        </label>

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="mt-6 w-full rounded-xl bg-teal-700 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "登录中…" : "登录"}
        </button>

        <p className="mt-4 text-center text-sm text-stone-500">
          还没有账号？{" "}
          <Link href="/register" className="text-teal-700 hover:underline">
            注册
          </Link>
        </p>
      </form>
    </div>
  );
}
