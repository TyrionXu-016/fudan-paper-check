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
    <header className="border-b border-stone-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">
            Fudan Paper Check
          </p>
          <h1 className="text-lg font-semibold text-stone-900">论文预检查</h1>
        </div>
        <nav className="flex items-center gap-2">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-full px-4 py-2 text-sm ${
                pathname.startsWith(link.href)
                  ? "bg-teal-700 text-white"
                  : "text-stone-600 hover:bg-stone-100"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="ml-4 hidden text-sm text-stone-500 sm:block">
            {user.name || user.email}
          </div>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className="ml-2 rounded-full border border-stone-200 px-4 py-2 text-sm text-stone-600 hover:bg-stone-50"
          >
            退出
          </button>
        </nav>
      </div>
    </header>
  );
}
