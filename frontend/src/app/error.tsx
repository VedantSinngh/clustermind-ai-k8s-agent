"use client";

import React, { useEffect } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Uncaught Next.js App Router error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between text-white font-sans">
      <div>
        <Navbar />
        <main className="max-w-4xl mx-auto px-6 py-16 text-center">
          <div className="bg-surface border border-rose-500/30 rounded-2xl p-8 shadow-2xl space-y-6">
            <div className="w-16 h-16 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400">
              <AlertTriangle className="w-8 h-8" />
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-white">System Error Occurred</h1>
            
            <p className="text-sm text-gray-300 max-w-md mx-auto leading-relaxed">
              An unexpected client error occurred while rendering the application component.
            </p>

            {error?.message && (
              <div className="p-3 bg-black/60 border border-borderSubtle rounded-lg text-xs font-mono text-rose-300 max-w-lg mx-auto truncate">
                {error.message}
              </div>
            )}

            <div>
              <button
                onClick={() => reset()}
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primaryHover text-white rounded-lg text-xs font-semibold shadow-lg shadow-primary/20 transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>
            </div>
          </div>
        </main>
      </div>
      <Footer />
    </div>
  );
}
