"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register, user, loading } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
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
      await register(email, password, name);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "注册失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_#ccfbf1,_transparent_35%),linear-gradient(180deg,#faf7f0,#f4f1ea)] px-6">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-3xl border border-stone-200 bg-white p-8 shadow-xl">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">Fudan Paper Check</p>
        <h1 className="mt-2 text-2xl font-semibold text-stone-900">注册</h1>

        <label className="mt-6 block text-sm text-stone-600">
          姓名
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-2 w-full rounded-xl border border-stone-200 px-4 py-3"
            placeholder="可选"
          />
        </label>

        <label className="mt-4 block text-sm text-stone-600">
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
          密码（至少 6 位）
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
          {submitting ? "注册中…" : "创建账号"}
        </button>

        <p className="mt-4 text-center text-sm text-stone-500">
          已有账号？{" "}
          <Link href="/login" className="text-teal-700 hover:underline">
            登录
          </Link>
        </p>
      </form>
    </div>
  );
}
