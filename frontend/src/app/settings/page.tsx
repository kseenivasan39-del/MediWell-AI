"use client";

import React from "react";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { Settings as SettingsIcon, Shield, Sliders, Database } from "lucide-react";

export default function SettingsPage() {
  return (
    <DesktopLayout pageTitle="Settings & Configuration" breadcrumb="Settings">
      <div className="space-y-6 max-w-4xl">
        <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
            <Sliders className="w-4 h-4 text-teal-600" />
            Wellness Drift Engine Configuration
          </h3>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
              <div>
                <span className="font-semibold text-slate-900 block">Drift Sensitivity Threshold</span>
                <span className="text-slate-500">Flags habit declines exceeding percentage from 14-day baseline.</span>
              </div>
              <span className="font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded border border-teal-200">
                15% Decline
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80">
              <div>
                <span className="font-semibold text-slate-900 block">Minimum History Period</span>
                <span className="text-slate-500">Required habit entries before drift analysis engages.</span>
              </div>
              <span className="font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
                7 Days
              </span>
            </div>
          </div>
        </div>

        <div className="p-6 bg-white rounded-xl border border-slate-200/90 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-teal-600" />
            Privacy & Sandbox Isolation
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            MediWell AI operates in full HIPAA/GDPR mock synthetic mode. All patient identifiers, telemetry streams, and vitals are non-PHI synthetic constructs generated exclusively for demonstration and development purposes.
          </p>
        </div>
      </div>
    </DesktopLayout>
  );
}
