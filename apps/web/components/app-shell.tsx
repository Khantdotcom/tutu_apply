"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const tabs = [
  { href: "/path", label: "Path" },
  { href: "/jobs", label: "Jobs" },
  { href: "/vault", label: "Vault" },
  { href: "/coach", label: "Coach" },
  { href: "/profile", label: "Profile" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col bg-white shadow md:max-w-2xl">
      <header className="sticky top-0 z-10 border-b bg-white p-4">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-lg font-semibold">TuTu Apply</h1>
          <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-medium">🔥 5 day streak</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full w-2/3 bg-brand" />
        </div>
        <p className="mt-1 text-xs text-slate-600">Chapter 1 • 420 XP</p>
      </header>
      <main className="flex-1 p-4">{children}</main>
      <nav className="sticky bottom-0 grid grid-cols-5 border-t bg-white text-xs">
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={`p-3 text-center ${pathname.startsWith(tab.href) ? "font-semibold text-brand" : "text-slate-500"}`}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
