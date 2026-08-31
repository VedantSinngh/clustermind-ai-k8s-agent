"use client";

import React from "react";
import { Cpu, ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full border-t border-borderSubtle bg-surface/30 py-6 mt-16">
      <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-2 font-mono">
          <Cpu className="w-4 h-4 text-primary" />
          <span>ClusterMind AI Engine v1.0 • Azure Container Apps & Groq LPU</span>
        </div>
        <div className="flex items-center gap-1.5 font-sans">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Built by <strong className="text-gray-300 font-medium">Vedant Singh</strong></span>
        </div>
      </div>
    </footer>
  );
}
