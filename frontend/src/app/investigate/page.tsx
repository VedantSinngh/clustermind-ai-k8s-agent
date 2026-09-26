"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ProgressRing from "@/components/ProgressRing";
import CodeBlock from "@/components/CodeBlock";
import RemediationModal from "@/components/RemediationModal";
import {
  Activity,
  Terminal,
  CheckCircle2,
  AlertTriangle,
  Play,
  Loader2,
  FileText,
  Layers,
  Network,
  ShieldCheck,
  Zap,
  Info
} from "lucide-react";
import { fetchApi } from "@/lib/api";

interface InvestigationResult {
  id: string;
  cluster_id: string;
  cluster_name?: string;
  namespace: string;
  root_cause?: string;
  suggested_fix?: string;
  suggested_command?: string;
  confidence_score?: number;
  raw_evidence?: any;
  llm_response?: any;
  status: string;
  progress_steps?: Array<{ step: string; status: string; timestamp: string }>;
}

export default function InvestigatePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialClusterId = searchParams.get("cluster_id") || "";

  const [clusters, setClusters] = useState<any[]>([]);
  const [selectedClusterId, setSelectedClusterId] = useState(initialClusterId);
  const [namespace, setNamespace] = useState("default");
  const [running, setRunning] = useState(false);
  const [activeStep, setActiveStep] = useState<string>("");
  const [investigation, setInvestigation] = useState<InvestigationResult | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "pods" | "logs" | "events" | "deployments" | "network">("summary");
  const [isRemediationOpen, setIsRemediationOpen] = useState(false);
  const [remediationLog, setRemediationLog] = useState<string | null>(null);
  const [userRole, setUserRole] = useState("viewer");

  useEffect(() => {
    fetchApi("/clusters").then((data) => {
      setClusters(data);
      if (data.length > 0) {
        if (!selectedClusterId) {
          setSelectedClusterId(data[0].id);
          setUserRole(data[0].role || "viewer");
        } else {
          const match = data.find((c: any) => c.id === selectedClusterId);
          if (match) setUserRole(match.role || "viewer");
        }
      }
    }).catch(console.error);
  }, [selectedClusterId]);

  const handleRunInvestigation = async () => {
    if (!selectedClusterId) return;
    setRunning(true);
    setInvestigation(null);
    setRemediationLog(null);

    setActiveStep("checking_pods");

    try {
      let data = await fetchApi("/investigations", {
        method: "POST",
        body: JSON.stringify({
          cluster_id: selectedClusterId,
          namespace: namespace,
        }),
      });

      // Poll background investigation until status changes from 'running'
      while (data.status === "running") {
        await new Promise((res) => setTimeout(res, 1000));
        data = await fetchApi(`/investigations/${data.id}`);
        if (data.progress_steps && data.progress_steps.length > 0) {
          const lastStep = data.progress_steps[data.progress_steps.length - 1];
          setActiveStep(lastStep.step);
        }
      }

      setActiveStep("completed");
      setInvestigation(data);
    } catch (err: any) {
      alert(`Investigation failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const steps = [
    { key: "checking_pods", label: "Inspecting Pod Health" },
    { key: "reading_logs", label: "Collecting Container Log Tails" },
    { key: "analyzing_events", label: "Filtering K8s Event Stream" },
    { key: "ai_reasoning", label: "Groq LLM SRE Reasoning Engine" },
  ];

  const selectedCluster = clusters.find((c) => c.id === selectedClusterId);

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between">
      <div>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* Top Control Bar */}
          <div className="bg-surface border border-borderSubtle rounded-xl p-6 mb-8 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white tracking-tight">AI Root Cause Troubleshooting</h1>
                  <p className="text-xs text-gray-400">Collect multi-layer K8s telemetry & reason over it with Groq Llama 3.3 70B</p>
                </div>
              </div>

              {/* Form Controls */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex flex-col">
                  <label className="text-[10px] font-mono uppercase text-gray-400 mb-1">Target Cluster</label>
                  <select
                    value={selectedClusterId}
                    onChange={(e) => {
                      setSelectedClusterId(e.target.value);
                      const match = clusters.find((c) => c.id === e.target.value);
                      if (match) setUserRole(match.role || "viewer");
                    }}
                    className="bg-black/60 border border-borderSubtle rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-primary"
                  >
                    {clusters.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col">
                  <label className="text-[10px] font-mono uppercase text-gray-400 mb-1">Namespace</label>
                  <input
                    type="text"
                    value={namespace}
                    onChange={(e) => setNamespace(e.target.value)}
                    className="bg-black/60 border border-borderSubtle rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-primary w-28"
                  />
                </div>

                <div className="flex flex-col justify-end">
                  <button
                    onClick={handleRunInvestigation}
                    disabled={running || !selectedClusterId}
                    className="flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primaryHover disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-lg shadow-primary/20 transition-all mt-4"
                  >
                    {running ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Collecting & Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-white" />
                        <span>Run Diagnostics</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Live Step Progress Stepper */}
            {running && (
              <div className="mt-6 pt-6 border-t border-borderSubtle grid grid-cols-2 md:grid-cols-4 gap-3">
                {steps.map((s, idx) => {
                  const isCurrent = activeStep === s.key;
                  return (
                    <div
                      key={s.key}
                      className={`p-3 rounded-lg border text-xs flex items-center gap-2.5 transition-all ${
                        isCurrent
                          ? "bg-primary/10 border-primary/40 text-primary font-medium"
                          : "bg-surfaceHover border-borderSubtle text-gray-400"
                      }`}
                    >
                      {isCurrent ? (
                        <Loader2 className="w-4 h-4 animate-spin text-primary shrink-0" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-gray-500 shrink-0" />
                      )}
                      <span className="truncate">{s.label}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Investigation Result Section */}
          {investigation && (
            <div className="space-y-6">
              {/* Root Cause Card & Confidence */}
              <div className="bg-surface border border-borderSubtle rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                  <div className="space-y-3 flex-1">
                    <div className="flex items-center gap-3">
                      <span className="px-2.5 py-1 text-[11px] font-mono font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-md">
                        {investigation.llm_response?.model_used || "Llama 3.3 70B"} Reasoning
                      </span>
                      <span className="text-xs font-mono text-gray-400">
                        Target: <strong className="text-white">{selectedCluster?.name}</strong> [{investigation.namespace}]
                      </span>
                    </div>

                    <h2 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                      <Zap className="w-5 h-5 text-amber-400 shrink-0" />
                      <span>Root Cause Diagnosis</span>
                    </h2>

                    <p className="text-sm text-gray-200 leading-relaxed font-sans bg-black/40 p-4 rounded-lg border border-borderSubtle">
                      {investigation.root_cause}
                    </p>

                    {/* Suggested Fix */}
                    <div className="pt-2">
                      <h3 className="text-xs font-semibold uppercase font-mono text-gray-400 mb-1">
                        Recommended Resolution Plan
                      </h3>
                      <p className="text-xs text-gray-300 leading-normal">{investigation.suggested_fix}</p>
                    </div>

                    {/* Code Command */}
                    {investigation.suggested_command && (
                      <div className="mt-4">
                        <CodeBlock command={investigation.suggested_command} />
                        <div className="flex items-center justify-between mt-2">
                          <button
                            onClick={() => setIsRemediationOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-all shadow-md shadow-emerald-900/30"
                          >
                            <ShieldCheck className="w-4 h-4" />
                            <span>Run This Fix (Human-in-the-Loop)</span>
                          </button>
                          <span className="text-[11px] font-mono text-gray-400">
                            Required Role: <strong className="text-primary">Operator</strong>
                          </span>
                        </div>
                      </div>
                    )}

                    {remediationLog && (
                      <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mt-3">
                        <strong>Remediation Audit Output:</strong> {remediationLog}
                      </div>
                    )}
                  </div>

                  {/* Radial Progress Ring */}
                  <div className="shrink-0 flex flex-col items-center bg-black/40 p-6 rounded-xl border border-borderSubtle">
                    <ProgressRing score={investigation.confidence_score || 0} size={110} strokeWidth={9} />
                    <div className="mt-4 text-center">
                      <p className="text-[11px] font-mono text-gray-400">Evidence Sourced</p>
                      <p className="text-xs font-semibold text-gray-200 mt-0.5">
                        {investigation.llm_response?.evidence_used?.length || 0} Telemetry Points
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Raw Evidence Tabs */}
              <div className="bg-surface border border-borderSubtle rounded-xl p-6 shadow-xl">
                <div className="flex items-center justify-between border-b border-borderSubtle pb-4 mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <FileText className="w-4 h-4 text-primary" />
                    <span>Raw Diagnostic Telemetry Payload</span>
                  </h3>
                  <div className="flex items-center gap-1 bg-black/60 p-1 rounded-lg border border-borderSubtle">
                    {(["summary", "pods", "logs", "events", "deployments", "network"] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-3 py-1 rounded text-xs font-mono uppercase transition-all ${
                          activeTab === tab
                            ? "bg-primary text-white font-semibold shadow-sm"
                            : "text-gray-400 hover:text-white"
                        }`}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tab Content */}
                <div className="bg-black/70 rounded-lg p-4 font-mono text-xs text-gray-300 border border-borderSubtle overflow-x-auto max-h-[400px]">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(
                      activeTab === "summary"
                        ? investigation.raw_evidence?.summary
                        : activeTab === "pods"
                        ? investigation.raw_evidence?.pods
                        : activeTab === "logs"
                        ? investigation.raw_evidence?.logs
                        : activeTab === "events"
                        ? investigation.raw_evidence?.events
                        : activeTab === "deployments"
                        ? investigation.raw_evidence?.deployments
                        : investigation.raw_evidence?.network,
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Confirmation Modal */}
      {investigation && (
        <RemediationModal
          isOpen={isRemediationOpen}
          onClose={() => setIsRemediationOpen(false)}
          investigationId={investigation.id}
          command={investigation.suggested_command || ""}
          userRole={userRole}
          onSuccess={(res) => setRemediationLog(res)}
        />
      )}

      <Footer />
    </div>
  );
}
