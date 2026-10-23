"use client";

import React, { useState, useEffect } from "react";
import { usePatient } from "@/context/PatientContext";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { api, CoachResponse, CoachSummary } from "@/lib/api";
import {
  Bot,
  ShieldCheck,
  Send,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Loader2,
  RefreshCw,
  FileText,
} from "lucide-react";

export default function CoachPage() {
  const { selectedPatient, createRecoveryProposal } = usePatient();
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [coachResponse, setCoachResponse] = useState<CoachResponse | null>(null);
  const [coachSummary, setCoachSummary] = useState<CoachSummary | null>(null);
  const [isGeneratingRecovery, setIsGeneratingRecovery] = useState(false);
  const [proposalSuccess, setProposalSuccess] = useState<string | null>(null);

  // Load initial coach summary
  useEffect(() => {
    let mounted = true;
    async function loadSummary() {
      try {
        const sum = await api.getCoachSummary(selectedPatient.id);
        if (mounted) setCoachSummary(sum);
      } catch (err) {
        console.warn("Coach summary unavailable:", err);
      }
    }
    loadSummary();
    return () => {
      mounted = false;
    };
  }, [selectedPatient.id]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const msg = inputMessage.trim();
    setInputMessage("");
    setIsLoading(true);
    setProposalSuccess(null);

    try {
      const res = await api.chatWithCoach(selectedPatient.id, msg);
      setCoachResponse(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestRecoveryProposal = async () => {
    setIsGeneratingRecovery(true);
    setProposalSuccess(null);
    try {
      const res = await api.generateCoachRecoverySuggestion(
        selectedPatient.id,
        "Requesting adaptive goals based on recent coach discussion."
      );
      setCoachResponse(res);
      setProposalSuccess(`Recovery proposal #${res.recovery_proposal_id} created! View and review on the Dashboard.`);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsGeneratingRecovery(false);
    }
  };

  return (
    <DesktopLayout pageTitle="AI Wellness Coach" breadcrumb="AI Coach">
      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Header Card */}
        <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600 shrink-0">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">Preventive Wellness Agent</h2>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  {coachSummary?.provider_name || "Offline Safety Engine"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluates habit telemetry, barriers, and adherence for {selectedPatient.name} ({selectedPatient.demoIdentifier}).
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg bg-teal-50 text-teal-800 border border-teal-200 shrink-0">
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            <span>Safety Guardrails Active</span>
          </div>
        </div>

        {/* Proactive Summary Card */}
        {coachSummary && (
          <div className="p-5 bg-slate-50 border border-slate-200/90 rounded-xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                Current Status: {coachSummary.overall_wellness_status}
              </span>
              <span className="text-[11px] text-slate-400">
                Primary Focus: {coachSummary.recommended_focus_area}
              </span>
            </div>
            <ul className="text-xs text-slate-600 space-y-1">
              {coachSummary.key_highlights.map((h, i) => (
                <li key={i} className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 shrink-0" />
                  <span>{h}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Chat / Interaction Box */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Bot className="w-4 h-4 text-teal-600" />
            <span>Ask or Reflect with Your Coach</span>
          </h3>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              onClick={() => setInputMessage("How is my overall routine adherence trending this week?")}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
            >
              Check adherence trend
            </button>
            <button
              type="button"
              onClick={() => setInputMessage("I'm feeling really fatigued after work and missing my evening walks.")}
              className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
            >
              Report fatigue barrier
            </button>
            <button
              type="button"
              onClick={() => setInputMessage("Should I stop taking my prescription metformin?")}
              className="px-2.5 py-1 rounded-full bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 font-medium transition-colors"
            >
              Test medical boundary
            </button>
          </div>

          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask for habit reflections, report barriers, or explore schedule adjustments..."
              className="flex-1 px-4 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white"
            />
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Send</span>
            </button>
          </form>

          {proposalSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{proposalSuccess}</span>
            </div>
          )}
        </div>

        {/* Render Structured Coach Output */}
        {coachResponse && (
          <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs space-y-5 animate-in fade-in duration-300">
            {/* Urgent / Emergency Notice */}
            {coachResponse.is_urgent_guidance && (
              <div className="p-4 bg-red-50 border border-red-300 rounded-xl text-red-900 text-xs font-medium flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="block text-sm font-bold text-red-950 mb-1">
                    Emergency Medical Guidance
                  </strong>
                  <p className="leading-relaxed">{coachResponse.summary}</p>
                </div>
              </div>
            )}

            {/* Main Summary */}
            {!coachResponse.is_urgent_guidance && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs leading-relaxed text-slate-800">
                <p className="font-medium">{coachResponse.summary}</p>
              </div>
            )}

            {/* Evidence-Linked Observations */}
            {coachResponse.observations.length > 0 && (
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-teal-600" />
                  <span>Ground-Truth Observations ({coachResponse.observations.length})</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {coachResponse.observations.map((obs, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-200/80 bg-white shadow-2xs text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold text-slate-500">
                          {obs.category}
                        </span>
                        <span
                          className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                            obs.observation_type === "observed"
                              ? "bg-teal-50 text-teal-800 border border-teal-200"
                              : obs.observation_type === "possible_explanation"
                              ? "bg-amber-50 text-amber-800 border border-amber-200"
                              : "bg-indigo-50 text-indigo-800 border border-indigo-200"
                          }`}
                        >
                          {obs.observation_type.replace("_", " ")}
                        </span>
                      </div>
                      <p className="text-slate-800 font-medium">{obs.statement}</p>
                      {obs.evidence_reference && (
                        <span className="text-[10px] text-slate-400 block italic">
                          Evidence: {obs.evidence_reference}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Practical Wellness Suggestions */}
            {coachResponse.practical_suggestions.length > 0 && (
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                  <span>Actionable Suggestions</span>
                </h4>
                <div className="space-y-2">
                  {coachResponse.practical_suggestions.map((sug, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-lg bg-teal-50/50 border border-teal-200/70 text-xs text-teal-950 space-y-1"
                    >
                      <span className="font-bold text-teal-900 block flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                        {sug.title}
                      </span>
                      <p className="text-teal-900">{sug.description}</p>
                      <p className="text-[11px] text-teal-700 italic">Rationale: {sug.rationale}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Follow-up Questions */}
            {coachResponse.follow_up_questions.length > 0 && (
              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
                  <span>Reflection Questions</span>
                </span>
                <ul className="list-disc pl-5 text-slate-600 space-y-1">
                  {coachResponse.follow_up_questions.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recovery Proposal CTA */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between flex-wrap gap-3">
              <span className="text-[11px] text-slate-400">
                Engine: {coachResponse.provider_name} ({coachResponse.model_name || "offline"})
              </span>

              <button
                type="button"
                onClick={handleRequestRecoveryProposal}
                disabled={isGeneratingRecovery}
                className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors"
              >
                {isGeneratingRecovery ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>Generate Adaptive Recovery Proposal</span>
              </button>
            </div>

            {/* Disclaimer */}
            <p className="text-[10px] text-slate-400 text-center pt-2">
              {coachResponse.safety_notice}
            </p>
          </div>
        )}
      </div>
    </DesktopLayout>
  );
}
