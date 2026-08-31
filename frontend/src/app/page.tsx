"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Lock, Mail, ArrowRight, ShieldCheck, Loader2 } from "lucide-react";
import { fetchApi, setAuthToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("vedant@clustermind.io");
  const [password, setPassword] = useState("ClusterMind2026!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        await fetchApi("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
      }

      const loginRes = await fetchApi("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setAuthToken(loginRes.access_token);
      router.push("/clusters");
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto w-full flex items-center justify-between py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <span className="font-semibold text-white tracking-tight text-lg">ClusterMind</span>
            <span className="ml-2 px-2 py-0.5 text-[10px] uppercase font-mono bg-primary/10 text-primary border border-primary/20 rounded">
              Production AI SRE
            </span>
          </div>
        </div>
      </div>

      {/* Auth Card */}
      <div className="max-w-md w-full mx-auto bg-surface border border-borderSubtle rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white tracking-tight mb-2">
            {isRegister ? "Create ClusterMind Account" : "Cluster Troubleshooting Portal"}
          </h1>
          <p className="text-xs text-gray-400">
            {isRegister ? "Register for enterprise RBAC multi-cluster access" : "Sign in to run AI root cause investigations"}
          </p>
        </div>

        {error && (
          <div className="p-3 mb-6 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5 font-mono">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="devops@company.com"
                className="w-full pl-9 pr-3 py-2.5 bg-black/50 border border-borderSubtle rounded-lg text-sm text-white focus:outline-none focus:border-primary transition-colors font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5 font-mono">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2.5 bg-black/50 border border-borderSubtle rounded-lg text-sm text-white focus:outline-none focus:border-primary transition-colors font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary hover:bg-primaryHover text-white rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>{isRegister ? "Create Account & Sign In" : "Sign In to ClusterMind"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-borderSubtle text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-xs text-gray-400 hover:text-primary transition-colors"
          >
            {isRegister ? "Already have an account? Sign in" : "Need cluster access? Register an account"}
          </button>
        </div>
      </div>

      {/* Footer Signature */}
      <div className="text-center py-4 text-xs text-gray-500 font-sans">
        Built by <strong className="text-gray-300 font-medium">Vedant Singh</strong> • AI Kubernetes Troubleshooting Agent
      </div>
    </div>
  );
}
