"use client";

import React, { useState } from "react";
import { Copy, Check, Terminal } from "lucide-react";

interface CodeBlockProps {
  command: string;
}

export default function CodeBlock({ command }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-borderSubtle bg-black/60 overflow-hidden my-3">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-borderSubtle bg-surface/80">
        <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
          <Terminal className="w-3.5 h-3.5 text-primary" />
          <span>Suggested kubectl Fix Command</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white px-2 py-1 rounded bg-surfaceHover hover:bg-surface border border-borderSubtle transition-all"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? "Copied!" : "Copy"}</span>
        </button>
      </div>
      <div className="p-3 font-mono text-xs text-emerald-400 overflow-x-auto whitespace-pre">
        <code>$ {command}</code>
      </div>
    </div>
  );
}
