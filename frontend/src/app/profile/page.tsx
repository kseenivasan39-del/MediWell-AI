"use client";

import React from "react";
import { usePatient } from "@/context/PatientContext";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { PatientOverview } from "@/components/dashboard/PatientOverview";
import { Stethoscope, FileText, CheckCircle2 } from "lucide-react";

export default function ProfilePage() {
  const { selectedPatient } = usePatient();

  return (
    <DesktopLayout pageTitle="Patient Profile" breadcrumb="Profile">
      <div className="space-y-6">
        <PatientOverview patient={selectedPatient} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
              <Stethoscope className="w-4 h-4 text-teal-600" />
              Documented Clinical Conditions
            </h3>
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80 mb-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-slate-900">
                  {selectedPatient.primaryCondition.name}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
                  {selectedPatient.primaryCondition.severity}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-2">
                {selectedPatient.primaryCondition.notes}
              </p>
              <span className="text-[10px] text-slate-400 block mt-2">
                Diagnosed: {selectedPatient.primaryCondition.diagnosedDate}
              </span>
            </div>
          </div>

          <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-teal-600" />
              Data Provenance & Audit Trail
            </h3>
            <div className="text-xs space-y-2 text-slate-600">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-400">Record Type</span>
                <span className="font-medium text-slate-800">Synthetic Clinical Benchmark</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-400">Quality Rating</span>
                <span className="font-medium text-slate-800">{selectedPatient.dataQualityRating}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-400">Last Telemetry Sync</span>
                <span className="font-medium text-slate-800">{selectedPatient.lastSyncedAt}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DesktopLayout>
  );
}
