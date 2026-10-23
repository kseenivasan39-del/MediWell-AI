"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from "recharts";

interface AdherenceChartProps {
  dailyTrend: Array<{
    day: string;
    adherence: number;
    hydration: number;
    activity: number;
    nutrition: number;
  }>;
  weeklyHistory: Array<{
    weekLabel: string;
    adherenceRate: number;
    targetRate: number;
  }>;
}

export function AdherenceChart({ dailyTrend, weeklyHistory }: AdherenceChartProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Wellness Analytics & Adherence
            </h3>
            <span className="text-xs text-slate-500 font-medium">
              Daily habit adherence breakdown over current period
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-xs bg-teal-600" />
              <span className="text-slate-600 font-medium">Adherence %</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-xs bg-cyan-400" />
              <span className="text-slate-600 font-medium">Hydration</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-xs bg-indigo-400" />
              <span className="text-slate-600 font-medium">Activity</span>
            </div>
          </div>
        </div>

        {/* Daily Breakdown Area Chart */}
        <div className="h-64 w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dailyTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="adherenceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0D9488" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0D9488" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 12, fill: "#64748B" }}
                axisLine={{ stroke: "#E2E8F0" }}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 12, fill: "#64748B" }}
                axisLine={false}
                tickLine={false}
                unit="%"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0F172A",
                  borderRadius: "8px",
                  border: "none",
                  color: "#FFFFFF",
                  fontSize: "12px",
                }}
                formatter={(value: any) => [`${value}%`]}
              />
              <Area
                type="monotone"
                dataKey="adherence"
                name="Overall Adherence"
                stroke="#0D9488"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#adherenceGrad)"
              />
              <Area
                type="monotone"
                dataKey="hydration"
                name="Hydration"
                stroke="#22D3EE"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                fillOpacity={0}
              />
              <Area
                type="monotone"
                dataKey="activity"
                name="Physical Activity"
                stroke="#818CF8"
                strokeWidth={1.5}
                strokeDasharray="2 2"
                fillOpacity={0}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Historical Weekly Bar Summary */}
      <div className="mt-4 pt-4 border-t border-slate-100">
        <span className="text-xs font-semibold text-slate-700 block mb-2">
          Multi-Week Adherence History (Target: 85%)
        </span>
        <div className="grid grid-cols-5 gap-2">
          {weeklyHistory.map((item, idx) => {
            const isBelowTarget = item.adherenceRate < item.targetRate;
            return (
              <div
                key={idx}
                className="p-2 rounded-lg bg-slate-50 border border-slate-200/80 text-center"
              >
                <span className="text-[10px] text-slate-400 block font-medium">
                  {item.weekLabel}
                </span>
                <span
                  className={`text-sm font-bold block mt-0.5 ${
                    isBelowTarget ? "text-amber-700" : "text-teal-700"
                  }`}
                >
                  {item.adherenceRate}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
