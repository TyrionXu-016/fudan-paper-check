"use client";

import { Navbar } from "@/components/Navbar";

type AppShellProps = {
  children: React.ReactNode;
  width?: "default" | "narrow" | "wide";
  showNav?: boolean;
};

export function AppShell({ children, width = "default", showNav = true }: AppShellProps) {
  const mainClass =
    width === "narrow"
      ? "app-main app-main--narrow"
      : width === "wide"
        ? "app-main app-main--wide"
        : "app-main";

  return (
    <div className="app-canvas">
      <div className="app-grain" aria-hidden />
      {showNav ? <Navbar /> : null}
      <main className={mainClass}>{children}</main>
    </div>
  );
}

export function LoadingScreen({ label = "加载中…" }: { label?: string }) {
  return (
    <div className="app-canvas flex min-h-screen items-center justify-center">
      <div className="app-grain" aria-hidden />
      <p className="relative z-10 font-[family-name:var(--font-sans)] text-sm text-ink-muted animate-pulse">
        {label}
      </p>
    </div>
  );
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-canvas relative">
      <div className="app-grain" aria-hidden />
      {children}
    </div>
  );
}
