"use client";

import React, { useState } from "react";
import { usePatient } from "@/context/PatientContext";
import {
  Bell,
  ChevronDown,
  User,
  Activity,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { AccessibilityMenu } from "@/components/ui/AccessibilityMenu";

interface DesktopHeaderProps {
  pageTitle: string;
  breadcrumb?: string;
  onMenuClick?: () => void;
}

export function DesktopHeader({
  pageTitle,
  breadcrumb = "Overview",
  onMenuClick,
}: DesktopHeaderProps) {
  const { patients, selectedPatient, setSelectedPatientId } = usePatient();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showPatientMenu, setShowPatientMenu] = useState(false);

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-4 md:px-6 lg:px-8 flex items-center justify-between shrink-0 sticky top-0 z-30 shadow-xs">
      {/* Brand on tablet (including 1024px), Title on desktop */}
      <div className="flex items-center gap-3">
        {/* Tablet brand icon and title */}
        <div className="flex xl:hidden items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-600">
            <Activity className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1">
              <span className="font-bold text-slate-900 tracking-tight text-sm">MediWell</span>
              <span className="text-[10px] px-1 py-0.2 rounded font-mono font-bold bg-teal-500/20 text-teal-700">AI</span>
            </div>
            <span className="text-[9px] text-slate-400 font-medium">Personalized Wellness</span>
          </div>
        </div>

        {/* Desktop Breadcrumb & Title */}
        <div className="hidden xl:flex flex-col">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <span>MediWell AI</span>
            <span>/</span>
            <span className="text-teal-700 font-semibold">{breadcrumb}</span>
          </div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight">{pageTitle}</h1>
        </div>
      </div>

      {/* Header Controls: Synthetic Patient Selector, Notifications, Profile */}
      <div className="flex items-center gap-4">
        {/* Synthetic Patient Selector */}
        <div className="relative">
          <button
            onClick={() => setShowPatientMenu(!showPatientMenu)}
            type="button"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100/80 transition-colors text-left focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 max-w-[200px] sm:max-w-none"
          >
            <div className="w-2 h-2 rounded-full bg-teal-500 shrink-0 animate-pulse" />
            <div className="flex flex-col min-w-0">
              <span className="text-[9px] sm:text-[10px] uppercase font-bold text-slate-500 tracking-wider truncate">
                Active Patient
              </span>
              <span className="text-xs font-semibold text-slate-800 truncate">
                {selectedPatient.name}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
          </button>

          {showPatientMenu && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1.5 border-b border-slate-100 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Select Synthetic Profile
              </div>
              {patients.map((p) => {
                const isSelected = p.id === selectedPatient.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      setSelectedPatientId(p.id);
                      setShowPatientMenu(false);
                    }}
                    className={`w-full text-left px-3 py-2 flex items-start gap-2.5 text-xs transition-colors ${
                      isSelected
                        ? "bg-teal-50 text-teal-900 font-medium"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <div className="mt-0.5">
                      {isSelected ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                      ) : (
                        <User className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900 truncate">{p.name}</span>
                        <span className="text-[10px] font-mono text-slate-500">{p.demoIdentifier}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">
                        {p.primaryCondition.name} ({p.primaryCondition.severity})
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Accessibility Tools Control */}
        <AccessibilityMenu />

        {/* Notifications Control */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-9 h-9 rounded-lg border border-slate-200 flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors relative"
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4" />
            {selectedPatient.driftAlert?.hasDrift && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-200 p-3 z-50">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-900">System Notifications</span>
                <span className="text-[10px] text-slate-500">Synthetic Environment</span>
              </div>
              <div className="mt-2 space-y-2 text-xs">
                {selectedPatient.driftAlert?.hasDrift ? (
                  <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-amber-900">Drift Detected</div>
                      <p className="text-[11px] text-amber-700 mt-0.5">
                        Adherence dropped by {selectedPatient.driftAlert.declinePercentage}% below baseline.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-lg bg-teal-50 border border-teal-200 flex items-start gap-2">
                    <Activity className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-teal-900">Habits Synchronized</div>
                      <p className="text-[11px] text-teal-700 mt-0.5">
                        All synthetic habit streams reflect the latest timestamp.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* User / Profile menu placeholder */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center text-xs font-semibold shadow-xs">
            MW
          </div>
        </div>
      </div>
    </header>
  );
}
