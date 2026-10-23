"use client";

import React from "react";
import { usePatient } from "@/context/PatientContext";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { PatientOverview } from "@/components/dashboard/PatientOverview";
import { WellnessMetricCard } from "@/components/dashboard/WellnessMetricCard";
import { DailyWellnessPlan } from "@/components/dashboard/DailyWellnessPlan";
import { AdherenceChart } from "@/components/dashboard/AdherenceChart";
import { WellnessDriftCard } from "@/components/dashboard/WellnessDriftCard";
import { CalendarIntegrationCard } from "@/components/dashboard/CalendarIntegrationCard";
import { AIInsightsPanel } from "@/components/dashboard/AIInsightsPanel";
import { ErrorState, LoadingState } from "@/components/ui/States";
import {
  calculateGoalStats,
  calculateAdherenceRate,
} from "@/lib/wellness-calculations";
import {
  TrendingUp,
  Target,
  CheckCircle2,
  CalendarCheck,
  Flame,
} from "lucide-react";

export default function DashboardPage() {
  const {
    selectedPatient,
    toggleGoalCompletion,
    isLoading,
    error,
  } = usePatient();

  if (isLoading) {
    return (
      <DesktopLayout pageTitle="Dashboard">
        <LoadingState message="Loading synthetic patient records..." />
      </DesktopLayout>
    );
  }

  if (error) {
    return (
      <DesktopLayout pageTitle="Dashboard">
        <ErrorState
          title="Telemetry Feed Error"
          message={error}
          retry={() => window.location.reload()}
        />
      </DesktopLayout>
    );
  }

  const goalStats = calculateGoalStats(selectedPatient.goals);
  const recentAdherence = calculateAdherenceRate(selectedPatient.recentHabitLogs);

  // Determine trend comparison if sufficient history exists (> 1 week)
  const history = selectedPatient.weeklyAdherenceHistory;
  const hasHistory = history.length >= 2;
  const currentWeekRate = history.length > 0 ? history[history.length - 1].adherenceRate : 0;
  const previousWeekRate = hasHistory ? history[history.length - 2].adherenceRate : 0;
  const trendDiff = currentWeekRate - previousWeekRate;

  return (
    <DesktopLayout pageTitle="Clinical Wellness Dashboard" breadcrumb="Dashboard">
      <div className="space-y-6">
        {/* Section A: Welcome & Patient Context */}
        <PatientOverview patient={selectedPatient} />

        {/* Section C: Wellness Overview Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <WellnessMetricCard
            title="Weekly Adherence"
            value={recentAdherence !== null ? `${recentAdherence}%` : "N/A"}
            subtitle="Calculated from logged habits"
            change={
              hasHistory
                ? {
                    value: `${Math.abs(trendDiff)}%`,
                    trend: trendDiff >= 0 ? "up" : "down",
                    label: "vs previous week",
                  }
                : undefined
            }
            icon={TrendingUp}
            badge={{
              text: recentAdherence && recentAdherence >= 80 ? "On Track" : "Needs Review",
              variant: recentAdherence && recentAdherence >= 80 ? "teal" : "amber",
            }}
          />

          <WellnessMetricCard
            title="Today's Goals"
            value={`${goalStats.completed} / ${goalStats.total}`}
            subtitle={`${goalStats.remaining} remaining today`}
            icon={CheckCircle2}
            badge={{
              text: `${goalStats.percentage}% Done`,
              variant: goalStats.percentage === 100 ? "teal" : "slate",
            }}
          />

          <WellnessMetricCard
            title="Plan Status"
            value={selectedPatient.planStatus}
            subtitle={selectedPatient.activePlanName}
            icon={Target}
            badge={{
              text: selectedPatient.dataQualityRating,
              variant: selectedPatient.dataQualityRating === "High Quality" ? "teal" : "slate",
            }}
          />

          <WellnessMetricCard
            title="Habit Momentum"
            value={hasHistory ? `${currentWeekRate}%` : "Calibrating"}
            subtitle={`Target: ${history.length > 0 ? history[history.length - 1].targetRate : 85}% benchmark`}
            icon={Flame}
            badge={{
              text: selectedPatient.driftAlert?.hasDrift ? "Drift Alert" : "Steady",
              variant: selectedPatient.driftAlert?.hasDrift ? "amber" : "teal",
            }}
          />
        </div>

        {/* Section E: Wellness Drift Detector */}
        <WellnessDriftCard driftAlert={selectedPatient.driftAlert} />

        {/* Section E.2: Direct Google Calendar Reminders Integration */}
        <CalendarIntegrationCard
          patientId={selectedPatient.id}
          patientName={selectedPatient.name}
          goals={selectedPatient.goals}
        />

        {/* Desktop 2-Column Grid: Section B & Section D */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Section B: Today's Wellness Plan (5 columns) */}
          <div className="lg:col-span-5">
            <DailyWellnessPlan
              goals={selectedPatient.goals}
              planName={selectedPatient.activePlanName}
              onToggleGoal={toggleGoalCompletion}
            />
          </div>

          {/* Section D: Wellness Analytics (7 columns) */}
          <div className="lg:col-span-7">
            <AdherenceChart
              dailyTrend={selectedPatient.dailyAdherenceTrend}
              weeklyHistory={selectedPatient.weeklyAdherenceHistory}
            />
          </div>
        </div>

        {/* Section F: AI Insights */}
        <AIInsightsPanel insights={selectedPatient.aiInsights} />
      </div>
    </DesktopLayout>
  );
}
