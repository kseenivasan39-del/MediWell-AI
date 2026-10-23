"use client";

import React from "react";
import { AIInsight } from "@/types/wellness";
import { Sparkles, CheckCircle, Info, ShieldCheck, HelpCircle } from "lucide-react";

interface AIInsightsPanelProps {
  insights: AIInsight[];
  isLoading?: boolean;
}

export function AIInsightsPanel({ insights, isLoading }: AIInsightsPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs">
        <div className="flex items-center gap-2 text-slate-400 text-xs">
          <div className="w-4 h-4 rounded-full border-2 border-teal-500 border-t-transparent animate-spin" />
          <span>Generating condition-aware clinical insights...</span>
        </div>
      </div>
    );
  }

  // Fallback when no insights exist (e.g. sparse patient)
  if (!insights || insights.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600" />
            <h3 className="text-base font-bold text-slate-900 tracking-tight">AI Wellness Insights</h3>
          </div>
          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200">
            Awaiting Data
          </span>
        </div>
        <div className="py-6 text-center text-xs text-slate-500 max-w-md mx-auto space-y-2">
          <p>
            No verified AI insights available for this profile yet. Insights require at least 5 logged habit entries and documented condition metrics.
          </p>
          <span className="text-[11px] text-slate-400 block">
            AI models do not generate predictive recommendations on insufficient telemetry.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-teal-600" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">AI Wellness Insights</h3>
          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
            Validated Suggestions
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
          <span>Condition-Constrained</span>
        </div>
      </div>

      {/* Distinction Banner: Clinical facts vs suggestions */}
      <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center gap-2 text-xs text-slate-600">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span>
          <strong>Clinical Guardrail:</strong> AI insights are advisory lifestyle recommendations synthesized from your logged habits and primary condition parameters. They do not supersede medical prescriptions.
        </span>
      </div>

      {/* Insights Cards */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight) => (
          <div
            key={insight.id}
            className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200/60">
                  {insight.category}
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {Math.round(insight.confidence * 100)}% Confidence
                </span>
              </div>

              <h4 className="text-sm font-bold text-slate-900 mt-2 tracking-tight">
                {insight.title}
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                {insight.observation}
              </p>

              <div className="mt-3 p-2.5 rounded-lg bg-teal-50/50 border border-teal-100 text-xs text-teal-900 font-medium">
                <span className="text-teal-700 font-semibold block text-[11px] mb-0.5">
                  Recommendation:
                </span>
                {insight.actionableRecommendation}
              </div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
              <span className="truncate max-w-[220px]">Basis: {insight.evidenceBasis}</span>
              <span className="font-semibold text-emerald-700 flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                Verified
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
