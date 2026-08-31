"use client";

import React from "react";

interface ProgressRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
}

export default function ProgressRing({ score, size = 90, strokeWidth = 8 }: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let colorClass = "text-emerald-500";
  if (score < 50) colorClass = "text-rose-500";
  else if (score < 80) colorClass = "text-amber-500";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className={`transition-all duration-1000 ease-out ${colorClass}`}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-center">
        <span className={`font-mono text-xl font-bold tracking-tight ${colorClass}`}>
          {score}%
        </span>
        <span className="text-[9px] uppercase font-mono text-gray-400">Confidence</span>
      </div>
    </div>
  );
}
