"use client";

import React from "react";
import { SyntheticPatient } from "@/types/wellness";
import { ShieldAlert, CheckCircle, Clock, Stethoscope, Sparkles } from "lucide-react";

interface PatientOverviewProps {
  patient: SyntheticPatient;
}

export function PatientOverview({ patient }: PatientOverviewProps) {
  const qualityBadge = {
    "High Quality": "bg-emerald-50 text-emerald-700 border-emerald-200",
    "Moderate": "bg-teal-50 text-teal-700 border-teal-200",
    "Sparse": "bg-amber-50 text-amber-700 border-amber-200",
    "Pending Verification": "bg-slate-100 text-slate-700 border-slate-200",
  }[patient.dataQualityRating];

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs">
      <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
        {/* Patient Identity & Clinical Context */}
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-lg shrink-0 shadow-sm">
            {patient.name
              .split(" ")
              .map((n) => n[0])
              .join("")}
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                {patient.name}
              </h2>
              <span className="text-xs px-2 py-0.5 rounded-md font-mono bg-slate-100 text-slate-600 border border-slate-200">
                {patient.demoIdentifier}
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {patient.age} yrs • {patient.gender}
              </span>
            </div>

            {/* Documented Condition Badge */}
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-teal-50 border border-teal-200/80 text-teal-800 text-xs font-semibold">
                <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                <span>{patient.primaryCondition.name}</span>
                <span className="text-teal-600 font-normal">({patient.primaryCondition.severity})</span>
              </div>

              {patient.secondaryConditions.map((cond) => (
                <span
                  key={cond.id}
                  className="text-xs px-2 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200"
                >
                  {cond.name}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Profile Completeness & Synthetic Guardrails Indicator */}
        <div className="flex items-center gap-6 w-full xl:w-auto justify-between xl:justify-end pt-4 xl:pt-0 border-t xl:border-t-0 border-slate-100">
          {/* Completeness Bar */}
          <div className="flex flex-col min-w-[160px]">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-500 font-medium">Profile Completeness</span>
              <span className="font-bold text-slate-800">{patient.profileCompleteness}%</span>
            </div>
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div
                className="bg-teal-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${patient.profileCompleteness}%` }}
              />
            </div>
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border self-start mt-1.5 ${qualityBadge}`}>
              {patient.dataQualityRating}
            </span>
          </div>

          {/* Synthetic Notice Banner */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50/70 border border-amber-200/80 text-amber-800 text-xs">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <div className="flex flex-col">
              <span className="font-bold text-[11px] leading-tight">Synthetic Record</span>
              <span className="text-[10px] text-amber-700">De-identified sandbox data</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
