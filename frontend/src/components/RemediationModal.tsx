"use client";

import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, X, ShieldAlert, Loader2 } from "lucide-react";
import { fetchApi } from "@/lib/api";

interface RemediationModalProps {
  isOpen: boolean;
  onClose: () => void;
  investigationId: string;
  command: string;
  userRole?: string;
  onSuccess: (result: string) => void;
}

export default function RemediationModal({
  isOpen,
  onClose,
  investigationId,
  command,
  userRole = "viewer",
  onSuccess,
}: RemediationModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isOperator = userRole === "operator";

  const handleExecute = async () => {
    if (!isOperator) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi("/remediations", {
        method: "POST",
        body: JSON.stringify({
          investigation_id: investigationId,
          command: command,
          confirm: true,
        }),
      });
      onSuccess(res.result);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to execute remediation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="bg-surface border border-borderSubtle rounded-xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          aria-label="Close modal"
          className="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-lg hover:bg-surfaceHover transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4 text-amber-400">
          <div className="w-10 h-10 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 id="modal-title" className="font-semibold text-white text-base">Human-in-the-Loop Confirmation</h3>
            <p className="text-xs text-gray-400">Explicit approval required before cluster write</p>
          </div>
        </div>

        {!isOperator ? (
          <div className="p-3 mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-mono">
            <strong>Access Denied:</strong> Your user role is set to &apos;viewer&apos;. Remediation execution requires &apos;operator&apos; authorization privileges on this cluster.
          </div>
        ) : (
          <div className="p-3 mb-4 rounded-lg bg-surfaceHover border border-borderSubtle text-xs text-gray-300">
            <p className="mb-2">Are you sure you want to execute the following remediation command on the target cluster?</p>
            <div className="font-mono bg-black/60 p-2 rounded text-emerald-400 border border-borderSubtle">
              $ {command}
            </div>
            <p className="mt-2 text-[11px] text-gray-400">
              * This execution will be permanently logged to the audit database (remediation_actions).
            </p>
          </div>
        )}

        {error && (
          <div className="p-3 mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white hover:bg-surfaceHover rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={!isOperator || loading}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              isOperator && !loading
                ? "bg-primary hover:bg-primaryHover text-white shadow-lg"
                : "bg-surfaceHover text-gray-600 cursor-not-allowed border border-borderSubtle"
            }`}
          >
            {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>{loading ? "Executing..." : "Confirm & Run Remediation"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
