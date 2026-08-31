"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, Shield, Terminal, History, LogOut } from "lucide-react";
import { removeAuthToken } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  if (pathname === "/") return null;

  const handleLogout = () => {
    removeAuthToken();
    router.push("/");
  };

  const navItems = [
    { label: "Clusters", href: "/clusters", icon: Activity },
    { label: "Live Troubleshoot", href: "/investigate", icon: Terminal },
    { label: "Audit History", href: "/history", icon: History },
  ];

  return (
    <nav className="w-full border-b border-borderSubtle bg-surface/50 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/clusters" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary group-hover:border-primary transition-colors">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white tracking-tight">ClusterMind</span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase font-mono font-medium bg-primary/10 text-primary border border-primary/20 rounded">
                AI SRE
              </span>
            </div>
            <p className="text-[11px] text-gray-400 font-mono">Autonomous K8s Agent</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-1 bg-surface px-3 py-1.5 rounded-lg border border-borderSubtle">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? "bg-primary text-white shadow-sm"
                    : "text-gray-400 hover:text-white hover:bg-surfaceHover"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* Account / Logout */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-md text-xs font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            RBAC Protected
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-surfaceHover border border-transparent hover:border-borderSubtle rounded-md transition-all"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
