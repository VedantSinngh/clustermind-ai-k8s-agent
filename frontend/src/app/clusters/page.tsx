"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Activity, Server, ArrowRight, Shield, Plus, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react";
import { fetchApi } from "@/lib/api";

interface Cluster {
  id: string;
  name: string;
  kubeconfig_secret_ref: string;
  org_id: string;
  created_at: string;
  role: string;
}

export default function ClustersPage() {
  const router = useRouter();
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadClusters = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi("/clusters");
      setClusters(data);
    } catch (err: any) {
      setError(err.message || "Failed to load registered clusters.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClusters();
  }, []);

  const handleSelectCluster = (clusterId: string) => {
    router.push(`/investigate?cluster_id=${clusterId}`);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between">
      <div>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 py-10">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Registered Clusters</h1>
              <p className="text-xs text-gray-400 mt-1">
                Select an authorized Kubernetes cluster to launch AI diagnostic telemetry and root cause analysis
              </p>
            </div>
            <button
              onClick={loadClusters}
              className="flex items-center gap-2 px-3.5 py-2 bg-surface border border-borderSubtle hover:border-primary/40 rounded-lg text-xs font-medium text-gray-300 hover:text-white transition-all w-fit"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh Clusters</span>
            </button>
          </div>

          {error && (
            <div className="p-4 mb-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
              {error}
            </div>
          )}

          {/* Cluster Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2].map((i) => (
                <div key={i} className="h-48 rounded-xl bg-surface/50 border border-borderSubtle animate-pulse p-6"></div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {clusters.map((cluster) => (
                <div
                  key={cluster.id}
                  onClick={() => handleSelectCluster(cluster.id)}
                  className="group cursor-pointer bg-surface border border-borderSubtle hover:border-primary/50 rounded-xl p-6 transition-all hover:shadow-xl hover:shadow-primary/5 flex flex-col justify-between"
                >
                  <div>
                    {/* Header line */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse"></span>
                        <span className="text-[11px] font-mono uppercase text-emerald-400">Connected</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 text-[10px] uppercase font-mono font-medium rounded border ${
                          cluster.role === "operator"
                            ? "bg-primary/10 text-primary border-primary/20"
                            : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                        }`}
                      >
                        {cluster.role}
                      </span>
                    </div>

                    <h3 className="text-base font-semibold text-white group-hover:text-primary transition-colors mb-2">
                      {cluster.name}
                    </h3>

                    <div className="space-y-1.5 font-mono text-xs text-gray-400">
                      <div className="flex items-center justify-between text-[11px]">
                        <span>Key Vault Secret:</span>
                        <span className="text-gray-300">{cluster.kubeconfig_secret_ref}</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span>Telemetry Mode:</span>
                        <span className="text-emerald-400">Active Real-Time</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-6 mt-6 border-t border-borderSubtle flex items-center justify-between">
                    <span className="text-xs font-medium text-primary group-hover:underline flex items-center gap-1">
                      Run AI Investigation
                    </span>
                    <div className="w-8 h-8 rounded-lg bg-surfaceHover border border-borderSubtle flex items-center justify-center text-gray-400 group-hover:text-white group-hover:border-primary/40 transition-colors">
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      <Footer />
    </div>
  );
}
