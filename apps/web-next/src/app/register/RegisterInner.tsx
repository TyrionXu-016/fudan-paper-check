"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { AuthShell } from "@/components/ui/AppShell";

export default function RegisterInner() {
  const { register, user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next") || "/mse/dashboard";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"advisor" | "student">("advisor");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const prefillEmail = searchParams.get("email");
    const prefillRole = searchParams.get("role");
    if (prefillEmail) setEmail(prefillEmail);
    if (prefillRole === "student" || prefillRole === "advisor") setRole(prefillRole);
  }, [searchParams]);

  if (!loading && user) {
    router.replace(nextPath);
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await register(email, password, name, role);
      router.push(nextPath);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "注册失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit} className="auth-panel">
        <p className="ui-label">Fudan Paper Check</p>
        <h1 className="display-title mt-2 text-3xl">注册</h1>
        <p className="mt-2 text-sm text-ink-muted">创建导师或学生账号，参与论文辅导流程。</p>

        <label className="mt-8 block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          姓名
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input-field"
            placeholder="可选"
          />
        </label>

        <label className="mt-4 block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
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
          密码（至少 6 位）
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
          />
        </label>

        <label className="mt-4 block font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          角色
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as "advisor" | "student")}
            className="input-field"
          >
            <option value="advisor">导师</option>
            <option value="student">学生</option>
          </select>
        </label>

        {error ? <p className="mt-4 text-sm text-vermillion">{error}</p> : null}

        <button type="submit" disabled={submitting} className="btn btn-primary mt-8 w-full py-3.5">
          {submitting ? "注册中…" : "创建账号"}
        </button>

        <p className="mt-6 text-center font-[family-name:var(--font-sans)] text-sm text-ink-muted">
          已有账号？{" "}
          <Link href="/login" className="text-vermillion hover:underline">
            登录
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
