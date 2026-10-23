"use client";

import React from "react";
import { DailyGoal } from "@/types/wellness";
import { CheckCircle2, Circle, Clock, Check } from "lucide-react";

interface DailyWellnessPlanProps {
  goals: DailyGoal[];
  planName: string;
  onToggleGoal: (goalId: string) => void;
}

export function DailyWellnessPlan({
  goals,
  planName,
  onToggleGoal,
}: DailyWellnessPlanProps) {
  const completedCount = goals.filter((g) => g.completed).length;
  const totalCount = goals.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const categoryColors = {
    nutrition: "bg-emerald-50 text-emerald-700 border-emerald-200",
    hydration: "bg-cyan-50 text-cyan-700 border-cyan-200",
    activity: "bg-teal-50 text-teal-700 border-teal-200",
    sleep: "bg-indigo-50 text-indigo-700 border-indigo-200",
    mindfulness: "bg-purple-50 text-purple-700 border-purple-200",
    medication: "bg-amber-50 text-amber-700 border-amber-200",
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
      {/* Header & Goal Counts */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Today&apos;s Wellness Plan</h3>
            <span className="text-xs text-slate-500 font-medium">{planName}</span>
          </div>
          <div className="text-right">
            <span className="text-sm font-bold text-slate-900">
              {completedCount} of {totalCount} Done
            </span>
            <span className="text-xs text-slate-400 block">{progressPercent}% Completed</span>
          </div>
        </div>

        {/* Linear Progress Bar */}
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mt-3">
          <div
            className="bg-teal-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Goals Checklist */}
        <div className="mt-4 space-y-2.5">
          {goals.map((goal) => {
            return (
              <div
                key={goal.id}
                onClick={() => onToggleGoal(goal.id)}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer flex items-start gap-3.5 select-none ${
                  goal.completed
                    ? "bg-slate-50/60 border-slate-200/60 text-slate-500"
                    : "bg-white border-slate-200 hover:border-teal-300 hover:bg-slate-50/40 text-slate-900 shadow-2xs"
                }`}
              >
                {/* Custom Checkbox */}
                <button
                  type="button"
                  aria-label={`Mark ${goal.title} as ${goal.completed ? "incomplete" : "complete"}`}
                  className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                    goal.completed
                      ? "bg-teal-600 text-white"
                      : "border border-slate-300 hover:border-teal-500 bg-white"
                  }`}
                >
                  {goal.completed && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-sm font-semibold tracking-tight ${
                        goal.completed ? "line-through text-slate-400" : "text-slate-800"
                      }`}
                    >
                      {goal.title}
                    </span>
                    <span
                      className={`text-[10px] font-medium px-2 py-0.5 rounded border capitalize ${
                        categoryColors[goal.category]
                      }`}
                    >
                      {goal.category}
                    </span>
                  </div>
                  <p
                    className={`text-xs mt-1 leading-relaxed ${
                      goal.completed ? "text-slate-400" : "text-slate-500"
                    }`}
                  >
                    {goal.description}
                  </p>
                  {goal.recommendedTime && (
                    <div className="flex items-center gap-1.5 mt-2 text-[11px] text-slate-400">
                      <Clock className="w-3 h-3" />
                      <span>Recommended: {goal.recommendedTime}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
        <span>Click any goal to toggle completion status</span>
        <span className="font-medium text-teal-700">Live Synced</span>
      </div>
    </div>
  );
}
