import React from "react";
import { LucideIcon, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface WellnessMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: {
    value: string;
    trend: "up" | "down" | "neutral";
    label: string;
  };
  icon: LucideIcon;
  badge?: {
    text: string;
    variant: "teal" | "amber" | "slate" | "indigo";
  };
}

export function WellnessMetricCard({
  title,
  value,
  subtitle,
  change,
  icon: Icon,
  badge,
}: WellnessMetricCardProps) {
  const badgeClasses = {
    teal: "bg-teal-50 text-teal-700 border-teal-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-200",
  };

  return (
    <div className="p-5 bg-white rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-all">
      <div className="flex items-start justify-between">
        <div className="flex flex-col">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {title}
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">
            {value}
          </span>
        </div>
        <div className="w-10 h-10 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-center text-slate-600">
          <Icon className="w-5 h-5 text-teal-600" />
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col gap-1 text-xs">
        <div className="flex items-center justify-between gap-1">
          {subtitle && (
            <span className="text-slate-500 truncate max-w-[170px]">{subtitle}</span>
          )}
          {badge && (
            <span
              className={`text-[11px] font-medium px-2 py-0.5 rounded-md border shrink-0 ${
                badgeClasses[badge.variant]
              }`}
            >
              {badge.text}
            </span>
          )}
        </div>

        {change && (
          <div className="flex items-center gap-1 font-medium mt-0.5">
            {change.trend === "up" && (
              <span className="flex items-center text-teal-700">
                <ArrowUpRight className="w-3.5 h-3.5" />
                {change.value}
              </span>
            )}
            {change.trend === "down" && (
              <span className="flex items-center text-rose-600">
                <ArrowDownRight className="w-3.5 h-3.5" />
                {change.value}
              </span>
            )}
            {change.trend === "neutral" && (
              <span className="flex items-center text-slate-500">
                <Minus className="w-3.5 h-3.5" />
                {change.value}
              </span>
            )}
            <span className="text-slate-400 font-normal">{change.label}</span>
          </div>
        )}
      </div>
    </div>
  );
}
