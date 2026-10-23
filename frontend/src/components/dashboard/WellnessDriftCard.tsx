"use client";

import React, { useState } from "react";
import { DriftAlert } from "@/types/wellness";
import { usePatient } from "@/context/PatientContext";
import {
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  Sparkles,
  Check,
  X,
  Edit2,
  Loader2,
} from "lucide-react";

interface WellnessDriftCardProps {
  driftAlert?: DriftAlert;
}

export function WellnessDriftCard({ driftAlert }: WellnessDriftCardProps) {
  const {
    backendDashboard,
    recoveryProposals,
    createRecoveryProposal,
    submitRecoveryDecision,
  } = usePatient();

  const [showRecoveryPlan, setShowRecoveryPlan] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeEditingId, setActiveEditingId] = useState<number | null>(null);
  const [editedTarget, setEditedTarget] = useState<number>(15);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const pendingProposal = recoveryProposals.find((p) => p.status === "pending");

  // Empty state: No drift detected
  if (!driftAlert || !driftAlert.hasDrift) {
    return (
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Wellness Drift Detector
              </h3>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
                Stable Adherence
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-xl">
              {driftAlert?.reason ||
                "No clinically meaningful decline detected. Recent 7-day adherence is aligned with previous baseline thresholds."}
            </p>
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <span className="text-xs text-slate-400 block font-medium">Detector Threshold</span>
          <span className="text-sm font-semibold text-slate-700">&gt; 15% Variance</span>
        </div>
      </div>
    );
  }

  const handleGenerateProposal = async () => {
    setIsGenerating(true);
    setActionSuccess(null);
    try {
      await createRecoveryProposal("Requested adaptive targets via Wellness Drift Card");
      setShowRecoveryPlan(true);
      setActionSuccess("Generated new adaptive recovery proposal for review!");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDecision = async (decision: "accepted" | "edited" | "rejected") => {
    if (!pendingProposal) return;
    setIsSubmitting(true);
    setActionSuccess(null);
    try {
      let revisedTargets = undefined;
      if (decision === "edited") {
        const firstGoal = pendingProposal.proposed_adjustments[0];
        revisedTargets = [
          {
            goal_id: firstGoal.goal_id,
            revised_target: editedTarget,
            notes: "Customized target via Dashboard",
          },
        ];
      }
      await submitRecoveryDecision(
        pendingProposal.id,
        decision,
        `Patient selected '${decision}' via UI`,
        revisedTargets
      );
      setActionSuccess(
        decision === "accepted"
          ? "Proposal accepted! Active plan goals updated."
          : decision === "edited"
          ? `Proposal updated with custom target (${editedTarget})!`
          : "Proposal rejected. Active plan remains unchanged."
      );
      setActiveEditingId(null);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Active Drift State
  return (
    <div className="bg-white rounded-xl border border-amber-300 p-6 shadow-xs relative overflow-hidden">
      {/* Top Warning Accent Bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-amber-500" />

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Wellness Drift Detected
              </h3>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
                <TrendingDown className="w-3.5 h-3.5" />
                -{driftAlert.declinePercentage}% Variance
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Adherence decline exceeds the 15% clinical alert threshold.
            </p>
          </div>
        </div>

        {/* Previous vs Recent Period Comparison */}
        <div className="flex items-center gap-3 bg-slate-50 border border-slate-200/80 rounded-lg p-2.5 text-xs w-full lg:w-auto justify-around">
          <div className="text-center px-2">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
              {driftAlert.previousPeriod}
            </span>
            <span className="text-sm font-bold text-slate-800">
              {driftAlert.previousAdherence}%
            </span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400" />
          <div className="text-center px-2">
            <span className="text-[10px] text-amber-700 uppercase tracking-wider block font-semibold">
              {driftAlert.recentPeriod}
            </span>
            <span className="text-sm font-bold text-amber-700">
              {driftAlert.recentAdherence}%
            </span>
          </div>
        </div>
      </div>

      {/* Flagged Reasons and Lagging Habits */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <span className="font-semibold text-slate-800 block mb-1">Root Cause Analysis</span>
          <p className="text-slate-600 leading-relaxed">{driftAlert.reason}</p>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/70">
          <span className="font-semibold text-slate-800 block mb-1">Primary Lagging Habits</span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {driftAlert.primaryLaggingHabits.length > 0 ? (
              driftAlert.primaryLaggingHabits.map((habit, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 font-medium text-[11px]"
                >
                  {habit}
                </span>
              ))
            ) : (
              <span className="text-slate-400 text-xs italic">All active scheduled habits</span>
            )}
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="mt-3 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Recovery Suggestion Action */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setShowRecoveryPlan(!showRecoveryPlan)}
            className="text-xs font-semibold text-amber-900 bg-amber-50 hover:bg-amber-100/80 border border-amber-200 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-700" />
            <span>{showRecoveryPlan ? "Hide Recovery Suggestions" : "Review Recovery Suggestions"}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>

          {!pendingProposal && (
            <button
              type="button"
              onClick={handleGenerateProposal}
              disabled={isGenerating}
              className="text-xs font-semibold text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-300 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
            >
              {isGenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Generate Adaptive Proposal</span>
            </button>
          )}
        </div>

        <span className="text-[11px] text-slate-400">
          Rule: Flagged when 7-day adherence is &ge;15% below baseline.
        </span>
      </div>

      {showRecoveryPlan && (
        <div className="mt-4 space-y-3">
          {pendingProposal ? (
            <div className="p-4 rounded-xl bg-teal-50/70 border border-teal-200 text-xs text-teal-950 animate-in fade-in duration-200">
              <div className="flex items-center justify-between pb-2 border-b border-teal-200/60 mb-2">
                <span className="font-bold text-teal-900 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  {pendingProposal.title}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal-100 text-teal-900">
                  Pending Review
                </span>
              </div>
              <p className="leading-relaxed text-teal-900 mb-3">{pendingProposal.rationale}</p>

              {/* Proposed Adjustments List */}
              <div className="space-y-2 mb-3">
                <span className="font-bold text-[11px] text-teal-950 uppercase tracking-wide block">
                  Proposed Target Modifications:
                </span>
                {pendingProposal.proposed_adjustments.map((adj, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-white border border-teal-200 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-semibold text-slate-900">{adj.habit_name}</span>
                      <span className="text-slate-500 block text-[11px]">
                        Current: {adj.current_target} {adj.unit} &rarr; Proposed:{" "}
                        <strong className="text-teal-700">{adj.proposed_target} {adj.unit}</strong>{" "}
                        ({adj.recommended_time || "Flexible"})
                      </span>
                    </div>

                    {activeEditingId === adj.goal_id ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          value={editedTarget}
                          onChange={(e) => setEditedTarget(parseFloat(e.target.value) || 0)}
                          className="w-16 px-1.5 py-0.5 border border-teal-400 rounded text-center text-xs"
                        />
                        <button
                          type="button"
                          onClick={() => handleDecision("edited")}
                          disabled={isSubmitting}
                          className="px-2 py-1 rounded bg-teal-600 text-white font-medium hover:bg-teal-700"
                        >
                          Save
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          setActiveEditingId(adj.goal_id);
                          setEditedTarget(adj.proposed_target || adj.current_target || 10);
                        }}
                        className="text-[11px] font-semibold text-teal-700 hover:text-teal-900 flex items-center gap-1"
                      >
                        <Edit2 className="w-3 h-3" />
                        <span>Edit</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Action Buttons: Accept / Reject */}
              <div className="pt-2 border-t border-teal-200/60 flex items-center gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => handleDecision("rejected")}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 text-xs font-semibold flex items-center gap-1"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Decline</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision("accepted")}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs"
                >
                  {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>Accept Eased Targets</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200/80 text-xs text-teal-950 animate-in fade-in duration-200">
              <span className="font-bold text-teal-900 block mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                Adaptive Habit Suggestion
              </span>
              <p className="leading-relaxed text-teal-800">{driftAlert.recoverySuggestion}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
