"use client";

import React from "react";
import { usePatient } from "@/context/PatientContext";
import { DesktopLayout } from "@/components/layout/DesktopLayout";
import { AdherenceChart } from "@/components/dashboard/AdherenceChart";
import { WellnessDriftCard } from "@/components/dashboard/WellnessDriftCard";

export default function AnalyticsPage() {
  const { selectedPatient } = usePatient();

  return (
    <DesktopLayout pageTitle="Progress & Analytics" breadcrumb="Analytics">
      <div className="space-y-6">
        <WellnessDriftCard driftAlert={selectedPatient.driftAlert} />
        <AdherenceChart
          dailyTrend={selectedPatient.dailyAdherenceTrend}
          weeklyHistory={selectedPatient.weeklyAdherenceHistory}
        />
      </div>
    </DesktopLayout>
  );
}
