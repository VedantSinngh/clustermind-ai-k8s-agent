"use client";

import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { History, Search, Filter, Calendar, Activity, ChevronRight } from "lucide-react";
import { fetchApi } from "@/lib/api";

interface HistoryItem {
  id: string;
  cluster_name: string;
  namespace: string;
  root_cause: string;
  suggested_command: string;
  confidence_score: number;
  status: string;
  created_at: string;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi("/investigations");
      setHistory(data);
    } catch (err: any) {
      setError(err.message || "Failed to load investigation audit log.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredHistory = history.filter(
    (item) =>
      item.cluster_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.root_cause?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.namespace?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between">
      <div>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                <History className="w-6 h-6 text-primary" />
                <span>Audit History Dashboard</span>
              </h1>
              <p className="text-xs text-gray-400 mt-1">
                Complete chronological log of all AI root cause diagnostic runs, confidence metrics, and executed remediations
              </p>
            </div>

            <div className="relative">
              <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search root cause, cluster..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 pr-4 py-2 bg-surface border border-borderSubtle rounded-lg text-xs text-white focus:outline-none focus:border-primary font-mono w-64"
              />
            </div>
          </div>

          {error && (
            <div className="p-4 mb-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
              {error}
            </div>
          )}

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-surface/50 border border-borderSubtle rounded-xl animate-pulse"></div>
              ))}
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="bg-surface border border-borderSubtle rounded-xl p-12 text-center text-gray-400 text-xs font-mono">
              No investigation records found in audit history.
            </div>
          ) : (
            <div className="bg-surface border border-borderSubtle rounded-xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-borderSubtle bg-surfaceHover text-gray-400 font-mono uppercase text-[10px]">
                      <th className="py-3.5 px-4 font-medium">Timestamp</th>
                      <th className="py-3.5 px-4 font-medium">Cluster</th>
                      <th className="py-3.5 px-4 font-medium">Namespace</th>
                      <th className="py-3.5 px-4 font-medium">Root Cause</th>
                      <th className="py-3.5 px-4 font-medium">Confidence</th>
                      <th className="py-3.5 px-4 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-borderSubtle font-sans">
                    {filteredHistory.map((item) => (
                      <tr key={item.id} className="hover:bg-surfaceHover/50 transition-colors">
                        <td className="py-3.5 px-4 font-mono text-[11px] text-gray-400">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-white">{item.cluster_name}</td>
                        <td className="py-3.5 px-4 font-mono text-[11px] text-gray-300">{item.namespace}</td>
                        <td className="py-3.5 px-4 text-gray-200 max-w-md truncate">{item.root_cause || "Analyzing..."}</td>
                        <td className="py-3.5 px-4 font-mono">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              (item.confidence_score || 0) >= 80
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : (item.confidence_score || 0) >= 50
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {item.confidence_score || 0}%
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`px-2 py-0.5 text-[10px] uppercase font-mono rounded ${
                              item.status === "completed"
                                ? "bg-emerald-500/10 text-emerald-400"
                                : "bg-amber-500/10 text-amber-400"
                            }`}
                          >
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      <Footer />
    </div>
  );
}
