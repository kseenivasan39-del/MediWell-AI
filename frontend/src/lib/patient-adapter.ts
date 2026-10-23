import { SyntheticPatient, DailyGoal, DriftAlert, AIInsight, Condition } from "@/types/wellness";
import { DashboardResponse, PatientListItem, TrendsResponse } from "@/lib/api";

export function mapBackendToSyntheticPatient(
  dashboard: DashboardResponse,
  trends?: TrendsResponse | null
): SyntheticPatient {
  const p = dashboard.patient;
  const drift = dashboard.drift_detector;

  const primaryCondition: Condition = {
    id: `cond-${dashboard.patient_id}`,
    name: p.primary_condition,
    category: "Preventive Care",
    severity: (["Mild", "Moderate", "Managed", "Under Review"].includes(p.condition_severity)
      ? p.condition_severity
      : "Under Review") as any,
    diagnosedDate: "2024-01-01",
    notes: p.condition_notes || "Documented clinical context and wellness recommendations.",
  };

  const secondaryConditions: Condition[] = (p.secondary_conditions || []).map((sec: any, idx: number) => ({
    id: `sec-${idx}`,
    name: typeof sec === "string" ? sec : sec.name || "Secondary Condition",
    category: "General",
    severity: typeof sec === "object" && sec.severity ? sec.severity : "Managed",
    diagnosedDate: typeof sec === "object" && sec.diagnosed_year ? `${sec.diagnosed_year}-01-01` : "2024-01-01",
    notes: typeof sec === "object" && sec.notes ? sec.notes : "Managed secondary clinical context.",
  }));

  const goals: DailyGoal[] = dashboard.today_goals.items.map((g) => ({
    id: String(g.goal_id),
    title: g.title,
    description: g.description || `${g.habit_name}: target ${g.target_value || 1} ${g.target_unit || ""}`.trim(),
    category: (["nutrition", "hydration", "activity", "sleep", "mindfulness", "medication"].includes(g.category.toLowerCase())
      ? g.category.toLowerCase()
      : "activity") as any,
    completed: g.is_completed_today,
    priority: (["low", "medium", "high"].includes(g.priority.toLowerCase())
      ? g.priority.toLowerCase()
      : "medium") as any,
    recommendedTime: g.recommended_time || undefined,
  }));

  const driftAlert: DriftAlert | undefined = drift.has_drift
    ? {
        hasDrift: true,
        declinePercentage: Math.abs(drift.percentage_point_change || 15.0),
        previousPeriod: "Baseline (21 days)",
        previousAdherence: Math.round(drift.baseline_adherence || 85),
        recentPeriod: drift.observation_window || "Recent 7 days",
        recentAdherence: Math.round(drift.current_adherence || 55),
        primaryLaggingHabits: drift.contributing_observations
          .filter((o) => o.category === "habit_decline" && o.habit_name)
          .map((o) => o.habit_name as string),
        reason: drift.flag_reason || "Adherence decreased significantly below your established clinical baseline.",
        recoverySuggestion: drift.recovery_suggestion || "Consider reviewing an adaptive recovery proposal with flexible targets.",
        thresholdMet: true,
      }
    : undefined;

  // Build AI Insights from contributing factors and coach highlights
  const aiInsights: AIInsight[] = (drift.contributing_observations || []).map((obs, idx) => ({
    id: `insight-${idx}`,
    category: obs.category === "user_reported_barrier"
      ? "Activity Modification"
      : obs.category === "timing_pattern"
      ? "Nutritional Timing"
      : "Clinical Preventive",
    title: obs.habit_name ? `Observation: ${obs.habit_name}` : "Habit Telemetry Observation",
    observation: obs.observation,
    actionableRecommendation: obs.barrier_reported
      ? `Address reported friction ('${obs.barrier_reported}') by adjusting schedule or reducing target duration.`
      : "Consider scheduling flexibility or smaller micro-habits to rebuild momentum.",
    evidenceBasis: `${obs.evidence_source} (${obs.date_range})`,
    confidence: 0.95,
    isVerified: true,
    generatedAt: dashboard.generated_at || new Date().toISOString(),
  }));

  // Build daily trend from backend trends if available, else synthetic fallback
  let dailyAdherenceTrend = [
    { day: "Mon", adherence: 85, hydration: 90, activity: 80, nutrition: 85 },
    { day: "Tue", adherence: 80, hydration: 85, activity: 75, nutrition: 80 },
    { day: "Wed", adherence: 75, hydration: 80, activity: 70, nutrition: 75 },
    { day: "Thu", adherence: 70, hydration: 75, activity: 65, nutrition: 70 },
    { day: "Fri", adherence: 65, hydration: 70, activity: 60, nutrition: 65 },
    { day: "Sat", adherence: 60, hydration: 65, activity: 55, nutrition: 60 },
    { day: "Sun", adherence: Math.round(dashboard.weekly_adherence.current_week_percentage || 55), hydration: 60, activity: 50, nutrition: 55 },
  ];

  if (trends && trends.points && trends.points.length > 0) {
    dailyAdherenceTrend = trends.points.slice(-7).map((pt) => {
      const dayName = new Date(pt.date).toLocaleDateString("en-US", { weekday: "short" });
      const rate = Math.round(pt.adherence_rate || 0);
      const hydrationVal = typeof pt.category_breakdown?.hydration === "number" ? pt.category_breakdown.hydration : rate;
      const activityVal = typeof pt.category_breakdown?.activity === "number" ? pt.category_breakdown.activity : rate;
      const nutritionVal = typeof pt.category_breakdown?.nutrition === "number" ? pt.category_breakdown.nutrition : rate;
      return {
        day: dayName,
        adherence: rate,
        hydration: Math.round(hydrationVal),
        activity: Math.round(activityVal),
        nutrition: Math.round(nutritionVal),
      };
    });
  }

  const weeklyAdherenceHistory = [
    {
      weekLabel: "Wk 1",
      adherenceRate: Math.round(dashboard.weekly_adherence.previous_week_percentage || 85),
      targetRate: 85,
      activeHabits: dashboard.today_goals.total,
    },
    {
      weekLabel: "Wk 2 (Current)",
      adherenceRate: Math.round(dashboard.weekly_adherence.current_week_percentage || 60),
      targetRate: 85,
      activeHabits: dashboard.today_goals.total,
    },
  ];

  return {
    id: p.synthetic_identifier,
    demoIdentifier: p.synthetic_identifier,
    name: p.display_name,
    age: p.age,
    gender: p.gender,
    primaryCondition,
    secondaryConditions,
    profileCompleteness: p.profile_completeness,
    dataQualityRating: (["High Quality", "Moderate", "Sparse", "Pending Verification"].includes(p.data_quality_rating)
      ? p.data_quality_rating
      : "Moderate") as any,
    activePlanName: dashboard.active_plan?.plan_name || "No Active Plan Prescribed",
    planStatus: (["Active", "Under Review", "Paused", "Optimized"].includes(dashboard.plan_status)
      ? dashboard.plan_status
      : "Under Review") as any,
    goals,
    recentHabitLogs: [],
    weeklyAdherenceHistory,
    dailyAdherenceTrend,
    driftAlert,
    aiInsights,
    lastSyncedAt: "Real-time API Sync",
  };
}
