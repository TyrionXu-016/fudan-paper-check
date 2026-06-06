"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

const links = [
  { href: "/mse/dashboard", label: "论文辅导" },
  { href: "/dashboard", label: "历史任务" },
  { href: "/upload", label: "上传检查" },
];

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  if (!user) return null;

  return (
    <header className="relative z-20 border-b border-ink/10 bg-paper-elevated/75 backdrop-blur-md">
      <div className="mx-auto flex max-w-[80rem] items-center justify-between gap-6 px-6 py-4">
        <Link href="/mse/dashboard" className="group flex items-center gap-4">
          <span
            className="hidden h-11 w-1 shrink-0 rounded-full bg-vermillion sm:block"
            aria-hidden
          />
          <div>
            <p className="ui-label">Fudan · Paper Check</p>
            <p className="display-title text-xl transition-colors group-hover:text-vermillion">
              论文预检查
            </p>
          </div>
        </Link>

        <nav className="flex flex-wrap items-center gap-1">
          {links.map((link) => {
            const active = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={active ? "nav-link nav-link--active" : "nav-link"}
              >
                {link.label}
              </Link>
            );
          })}
          <span className="mx-2 hidden h-5 w-px bg-ink/15 sm:block" aria-hidden />
          <span className="hidden max-w-[12rem] truncate font-[family-name:var(--font-sans)] text-xs text-ink-muted sm:block">
            {user.name || user.email}
          </span>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="btn btn-ghost ml-1"
          >
            退出
          </button>
        </nav>
      </div>
    </header>
  );
}
