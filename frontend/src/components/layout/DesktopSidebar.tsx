"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardList,
  LineChart,
  Bot,
  UserCheck,
  Settings,
  ShieldCheck,
  HeartPulse,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "My Wellness Plan", href: "/wellness-plan", icon: ClipboardList },
  { label: "Progress & Analytics", href: "/analytics", icon: LineChart },
  { label: "AI Wellness Coach", href: "/coach", icon: Bot, badge: "Beta" },
  { label: "Patient Profile", href: "/profile", icon: UserCheck },
  { label: "Settings", href: "/settings", icon: Settings },
];

interface DesktopSidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

export function DesktopSidebar({
  isCollapsed = false,
  onToggleCollapse,
  isOpenMobile = false,
  onCloseMobile,
}: DesktopSidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Tablet / Mobile Backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-40 md:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`bg-[#0F172A] text-slate-300 flex flex-col shrink-0 border-r border-slate-800 select-none min-h-screen transition-all duration-300 z-50 fixed lg:static inset-y-0 left-0 ${
          isOpenMobile ? "translate-x-0 w-64 shadow-2xl" : "-translate-x-full lg:translate-x-0"
        } ${isCollapsed ? "lg:w-20" : "lg:w-64"}`}
      >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80 bg-[#0B1120]">
        <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
          <HeartPulse className="w-5 h-5 text-teal-400" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-white tracking-tight text-base">MediWell</span>
            <span className="text-xs px-1.5 py-0.5 rounded font-mono font-medium bg-teal-500/20 text-teal-300 border border-teal-500/30">AI</span>
          </div>
          <span className="text-[11px] text-slate-400">Preventive Health OS</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {!isCollapsed && (
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Clinical Navigation
          </div>
        )}
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              title={isCollapsed ? item.label : undefined}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isCollapsed ? "justify-center px-2" : ""
              } ${
                isActive
                  ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-teal-400" : "text-slate-400"}`} />
              {!isCollapsed && <span className="flex-1 truncate">{item.label}</span>}
              {!isCollapsed && item.badge && (
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-teal-300 border border-teal-500/20">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Safety & Compliance Notice */}
      {!isCollapsed && (
        <div className="p-4 m-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs space-y-2">
          <div className="flex items-center gap-2 text-teal-400 font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>Synthetic Data Mode</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Operating in sandboxed demonstration mode. No real PHI is processed or retained.
          </p>
        </div>
      )}

      {/* User / Clinician session badge */}
      <div className={`p-4 border-t border-slate-800 bg-[#0B1120] flex items-center ${isCollapsed ? "justify-center" : "gap-3"}`}>
        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-medium text-slate-200 shrink-0">
          DR
        </div>
        {!isCollapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-semibold text-slate-200 truncate">Dr. R. Alverez</span>
            <span className="text-[10px] text-slate-400 truncate">Clinical Wellness Lead</span>
          </div>
        )}
      </div>
    </aside>
    </>
  );
}
