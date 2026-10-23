"use client";

import React from "react";
import { usePatient } from "@/context/PatientContext";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { DailyWellnessPlan } from "@/components/dashboard/DailyWellnessPlan";
import { Stethoscope, CheckCircle, Shield } from "lucide-react";

export default function WellnessPlanPage() {
  const { selectedPatient, toggleGoalCompletion } = usePatient();

  return (
    <DesktopLayout pageTitle="My Wellness Plan" breadcrumb="My Wellness Plan">
      <div className="space-y-6">
        {/* Plan Header Card */}
        <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs uppercase font-bold text-teal-700 bg-teal-50 px-2.5 py-0.5 rounded border border-teal-200">
                {selectedPatient.planStatus} Protocol
              </span>
              <h2 className="text-xl font-bold text-slate-900 mt-2">
                {selectedPatient.activePlanName}
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Customized for {selectedPatient.name}&apos;s condition: {selectedPatient.primaryCondition.name} ({selectedPatient.primaryCondition.severity}).
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
              <Stethoscope className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Plan Execution */}
        <DailyWellnessPlan
          goals={selectedPatient.goals}
          planName={selectedPatient.activePlanName}
          onToggleGoal={toggleGoalCompletion}
        />
      </div>
    </DesktopLayout>
  );
}
