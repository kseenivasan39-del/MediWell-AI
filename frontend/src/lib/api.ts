import { z } from "zod";

// ============================================================================
// 1. Zod Schemas for FastAPI Backend Endpoints
// ============================================================================

export const PatientListItemSchema = z.object({
  id: z.number(),
  synthetic_identifier: z.string(),
  display_name: z.string(),
  age: z.number(),
  gender: z.string(),
  primary_condition: z.string(),
  condition_severity: z.string(),
  profile_completeness: z.number(),
  data_quality_rating: z.string(),
  active_plan_name: z.string().nullable().optional(),
  has_active_drift: z.boolean().default(false),
  is_synthetic: z.boolean().default(true),
});
export type PatientListItem = z.infer<typeof PatientListItemSchema>;

export const GoalTodaySchema = z.object({
  goal_id: z.number(),
  habit_id: z.number(),
  habit_code: z.string(),
  habit_name: z.string(),
  category: z.string(),
  title: z.string(),
  description: z.string().nullable().optional(),
  target_value: z.number().nullable().optional(),
  target_unit: z.string().nullable().optional(),
  priority: z.string(),
  recommended_time: z.string().nullable().optional(),
  is_completed_today: z.boolean(),
  today_log_id: z.number().nullable().optional(),
  today_numeric_value: z.number().nullable().optional(),
  today_user_reported_barrier: z.string().nullable().optional(),
});
export type GoalToday = z.infer<typeof GoalTodaySchema>;

export const ContributingObservationSchema = z.object({
  category: z.string(),
  habit_id: z.number().nullable().optional(),
  habit_name: z.string().nullable().optional(),
  observation: z.string(),
  evidence_source: z.string(),
  date_range: z.string(),
  barrier_reported: z.string().nullable().optional(),
  severity: z.string().default("moderate"),
});
export type ContributingObservation = z.infer<typeof ContributingObservationSchema>;

export const DriftDetectorSummarySchema = z.object({
  has_drift: z.boolean(),
  status: z.string(),
  baseline_adherence: z.number().nullable().optional(),
  current_adherence: z.number().nullable().optional(),
  percentage_point_change: z.number().nullable().optional(),
  severity: z.string().nullable().optional(),
  observation_window: z.string().nullable().optional(),
  data_sufficiency: z.string().nullable().optional(),
  flag_reason: z.string().nullable().optional(),
  recovery_suggestion: z.string().nullable().optional(),
  contributing_observations: z.array(ContributingObservationSchema).default([]),
  recovery_proposal_call_to_action: z.string().nullable().optional(),
  has_pending_recovery_proposal: z.boolean().default(false),
  pending_recovery_proposal_id: z.number().nullable().optional(),
});
export type DriftDetectorSummary = z.infer<typeof DriftDetectorSummarySchema>;

export const DashboardResponseSchema = z.object({
  patient_id: z.number(),
  patient: z.object({
    synthetic_identifier: z.string(),
    display_name: z.string(),
    age: z.number(),
    gender: z.string(),
    primary_condition: z.string(),
    condition_severity: z.string(),
    condition_notes: z.string().nullable().optional(),
    secondary_conditions: z.array(z.any()).default([]),
    profile_completeness: z.number(),
    data_quality_rating: z.string(),
    preferences: z.record(z.string(), z.any()).default({}),
    is_synthetic: z.boolean().default(true),
  }),
  plan_status: z.string(),
  active_plan: z.object({
    id: z.number(),
    plan_name: z.string(),
    version: z.string(),
    status: z.string(),
    description: z.string().nullable().optional(),
    goals: z.array(z.any()).default([]),
  }).nullable().optional(),
  today_goals: z.object({
    total: z.number(),
    completed: z.number(),
    remaining: z.number(),
    completion_percentage: z.number(),
    items: z.array(GoalTodaySchema).default([]),
  }),
  weekly_adherence: z.object({
    current_week_percentage: z.number().nullable().optional(),
    previous_week_percentage: z.number().nullable().optional(),
    percentage_point_delta: z.number().nullable().optional(),
    trend_direction: z.string().nullable().optional(),
    data_status: z.string(),
  }),
  habit_momentum: z.object({
    score: z.number().nullable().optional(),
    label: z.string(),
    streak_days: z.number().default(0),
    formula_documented: z.string().optional(),
  }),
  recent_measurements: z.array(
    z.object({
      id: z.number(),
      measurement_type: z.string(),
      value: z.number(),
      unit: z.string(),
      recorded_at: z.string(),
      context_notes: z.string().nullable().optional(),
    })
  ).default([]),
  profile_completeness: z.object({
    profile_completeness: z.number(),
    data_quality_rating: z.string(),
    has_condition_context: z.boolean(),
    has_active_plan: z.boolean(),
    total_goals_configured: z.number(),
    total_logged_days: z.number(),
    has_sufficient_history: z.boolean(),
    missing_fields: z.array(z.string()).default([]),
  }),
  drift_detector: DriftDetectorSummarySchema,
  generated_at: z.string().optional(),
});
export type DashboardResponse = z.infer<typeof DashboardResponseSchema>;

export const AdherenceAnalyticsSchema = z.object({
  window_days: z.number(),
  start_date: z.string(),
  end_date: z.string(),
  eligible_occurrences: z.number(),
  completed_occurrences: z.number(),
  adherence_percentage: z.number().nullable().optional(),
  previous_period_adherence_percentage: z.number().nullable().optional(),
  percentage_point_delta: z.number().nullable().optional(),
  trend_direction: z.string().nullable().optional(),
  data_status: z.string(),
});
export type AdherenceAnalytics = z.infer<typeof AdherenceAnalyticsSchema>;

export const TrendPointSchema = z.object({
  date: z.string(),
  scheduled_goals: z.number(),
  completed_goals: z.number(),
  adherence_rate: z.number().nullable().optional(),
  category_breakdown: z.record(z.string(), z.number().nullable().optional()).default({}),
});

export const TrendsResponseSchema = z.object({
  patient_id: z.number(),
  synthetic_identifier: z.string(),
  window_days: z.number(),
  start_date: z.string(),
  end_date: z.string(),
  points: z.array(TrendPointSchema).default([]),
  overall_adherence: z.number().nullable().optional(),
  data_status: z.string(),
});
export type TrendsResponse = z.infer<typeof TrendsResponseSchema>;

export const ProposedAdjustmentItemSchema = z.object({
  goal_id: z.number(),
  habit_id: z.number(),
  habit_name: z.string(),
  current_target: z.number().nullable().optional(),
  proposed_target: z.number().nullable().optional(),
  unit: z.string().nullable().optional(),
  current_frequency: z.string().nullable().optional(),
  proposed_frequency: z.string().nullable().optional(),
  recommended_time: z.string().nullable().optional(),
  adjustment_type: z.string(),
});
export type ProposedAdjustmentItem = z.infer<typeof ProposedAdjustmentItemSchema>;

export const RecoveryProposalSchema = z.object({
  id: z.number(),
  patient_id: z.number(),
  plan_id: z.number(),
  drift_event_id: z.number().nullable().optional(),
  title: z.string(),
  rationale: z.string(),
  status: z.enum(["pending", "accepted", "edited", "rejected"]),
  decision_notes: z.string().nullable().optional(),
  proposed_adjustments: z.array(ProposedAdjustmentItemSchema).default([]),
  barrier_question: z.string().nullable().optional(),
  created_at: z.string(),
  decided_at: z.string().nullable().optional(),
});
export type RecoveryProposal = z.infer<typeof RecoveryProposalSchema>;

export const CoachObservationSchema = z.object({
  category: z.string(),
  observation_type: z.enum(["observed", "possible_explanation", "suggestion"]),
  statement: z.string(),
  evidence_reference: z.string().nullable().optional(),
});

export const PracticalSuggestionSchema = z.object({
  title: z.string(),
  description: z.string(),
  rationale: z.string(),
});

export const CoachResponseSchema = z.object({
  patient_id: z.number(),
  synthetic_identifier: z.string(),
  summary: z.string(),
  observations: z.array(CoachObservationSchema).default([]),
  practical_suggestions: z.array(PracticalSuggestionSchema).default([]),
  follow_up_questions: z.array(z.string()).default([]),
  recovery_proposal_id: z.number().nullable().optional(),
  recovery_proposal_title: z.string().nullable().optional(),
  data_sufficiency: z.string(),
  safety_notice: z.string(),
  is_urgent_guidance: z.boolean().default(false),
  provider_name: z.string(),
  model_name: z.string().nullable().optional(),
  generated_at: z.string(),
});
export type CoachResponse = z.infer<typeof CoachResponseSchema>;

export const CoachSummarySchema = z.object({
  patient_id: z.number(),
  synthetic_identifier: z.string(),
  display_name: z.string(),
  overall_wellness_status: z.string(),
  key_highlights: z.array(z.string()).default([]),
  recommended_focus_area: z.string().nullable().optional(),
  has_active_drift: z.boolean().default(false),
  pending_recovery_proposal_id: z.number().nullable().optional(),
  provider_name: z.string(),
  generated_at: z.string(),
});
export type CoachSummary = z.infer<typeof CoachSummarySchema>;

export const CalendarStatusSchema = z.object({
  is_configured: z.boolean(),
  is_connected: z.boolean(),
  account_email: z.string().nullable().optional(),
  calendar_id: z.string().default("primary"),
  timezone: z.string().default("Asia/Kolkata"),
  connected_at: z.string().nullable().optional(),
  last_synced_at: z.string().nullable().optional(),
  last_sync_status: z.string().nullable().optional(),
  last_sync_error: z.string().nullable().optional(),
  synced_events_count: z.number().default(0),
});
export type CalendarStatusResponse = z.infer<typeof CalendarStatusSchema>;

export const SyncedEventItemSchema = z.object({
  goal_id: z.number(),
  google_event_id: z.string(),
  title: z.string(),
  scheduled_time: z.string(),
  html_link: z.string().nullable().optional(),
  action: z.string(),
});
export type SyncedEventItem = z.infer<typeof SyncedEventItemSchema>;

export const ReminderSyncResultSchema = z.object({
  success: z.boolean(),
  synced_count: z.number(),
  skipped_count: z.number(),
  failed_count: z.number(),
  events: z.array(SyncedEventItemSchema).default([]),
  errors: z.array(z.string()).default([]),
  delivery_notice: z.string(),
});
export type ReminderSyncResult = z.infer<typeof ReminderSyncResultSchema>;



// ============================================================================
// 2. Centralized Typed API Client
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  schema?: z.ZodSchema<T>
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let errData;
      try {
        errData = await res.json();
      } catch {
        errData = await res.text();
      }
      throw new ApiError(res.status, errData?.detail || `HTTP ${res.status} error from ${endpoint}`, errData);
    }

    const json = await res.json();
    if (schema) {
      const parsed = schema.safeParse(json);
      if (!parsed.success) {
        console.warn(`[API validation warning on ${endpoint}]:`, parsed.error);
        return json as T; // Fallback to raw json if schema has slight extra fields
      }
      return parsed.data;
    }
    return json as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new ApiError(408, `Request to ${endpoint} timed out.`);
    }
    throw err;
  }
}

export const api = {
  // Patients
  getPatients: () => request<PatientListItem[]>("/patients", {}, z.array(PatientListItemSchema)),
  getPatientDashboard: (patientId: string) =>
    request<DashboardResponse>(`/patients/${patientId}/dashboard`, {}, DashboardResponseSchema),

  // Today Goals & Habit Logs
  getTodayGoals: (patientId: string) =>
    request<GoalToday[]>(`/patients/${patientId}/goals/today`, {}, z.array(GoalTodaySchema)),
  createHabitLog: (
    patientId: string,
    data: { habit_id: number; log_date: string; is_completed: boolean; numeric_value?: number; notes?: string; user_reported_barrier?: string }
  ) =>
    request<any>(`/patients/${patientId}/habits/logs`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateHabitLog: (
    logId: number,
    data: { is_completed?: boolean; numeric_value?: number; notes?: string; user_reported_barrier?: string }
  ) =>
    request<any>(`/habit-logs/${logId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Analytics
  getAdherenceAnalytics: (patientId: string, windowDays: number = 7) =>
    request<AdherenceAnalytics>(`/patients/${patientId}/analytics/adherence?window_days=${windowDays}`, {}, AdherenceAnalyticsSchema),
  getTrends: (patientId: string, days: number = 14) =>
    request<TrendsResponse>(`/patients/${patientId}/analytics/trends?days=${days}`, {}, TrendsResponseSchema),
  getMeasurements: (patientId: string, limit: number = 10) =>
    request<any[]>(`/patients/${patientId}/measurements?limit=${limit}`),

  // Drift Detector
  getDriftStatus: (patientId: string) => request<any>(`/patients/${patientId}/drift`),
  analyzeDrift: (patientId: string, persistEvent: boolean = true) =>
    request<any>(`/patients/${patientId}/drift/analyze`, {
      method: "POST",
      body: JSON.stringify({ persist_event: persistEvent }),
    }),
  getDriftHistory: (patientId: string) => request<any[]>(`/patients/${patientId}/drift/history`),

  // Recovery Proposals
  getRecoveryProposals: (patientId: string, statusFilter?: string) => {
    const query = statusFilter ? `?status_filter=${statusFilter}` : "";
    return request<RecoveryProposal[]>(`/patients/${patientId}/recovery-proposals${query}`, {}, z.array(RecoveryProposalSchema));
  },
  createRecoveryProposal: (patientId: string, customNotes?: string) =>
    request<RecoveryProposal>(`/patients/${patientId}/recovery-proposals`, {
      method: "POST",
      body: JSON.stringify({ custom_notes: customNotes }),
    }, RecoveryProposalSchema),
  submitRecoveryDecision: (
    proposalId: number,
    decision: "accepted" | "edited" | "rejected",
    notes?: string,
    userRevisedTargets?: any[]
  ) =>
    request<RecoveryProposal>(`/recovery-proposals/${proposalId}/decision`, {
      method: "POST",
      body: JSON.stringify({
        decision,
        decision_notes: notes,
        user_revised_targets: userRevisedTargets,
      }),
    }, RecoveryProposalSchema),

  // AI Wellness Coach
  chatWithCoach: (patientId: string, message: string) =>
    request<CoachResponse>(`/patients/${patientId}/coach`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }, CoachResponseSchema),
  getCoachSummary: (patientId: string) =>
    request<CoachSummary>(`/patients/${patientId}/coach/summary`, {}, CoachSummarySchema),
  generateCoachRecoverySuggestion: (patientId: string, customContext?: string) =>
    request<CoachResponse>(`/patients/${patientId}/coach/recovery-suggestion`, {
      method: "POST",
      body: JSON.stringify({ custom_context: customContext }),
    }, CoachResponseSchema),

  // Google Calendar Integration
  getCalendarStatus: () =>
    request<CalendarStatusResponse>("/calendar/status", {}, CalendarStatusSchema),
  getCalendarConnectUrl: () =>
    request<{ auth_url: string; state: string }>("/calendar/connect"),
  disconnectCalendar: () =>
    request<{ success: boolean; message: string }>("/calendar/disconnect", {
      method: "POST",
    }),
  syncCalendarReminders: (
    patientId?: string,
    goalIds?: number[],
    customTimes?: Record<number, string>
  ) =>
    request<ReminderSyncResult>("/calendar/reminders/sync", {
      method: "POST",
      body: JSON.stringify({
        patient_id: patientId,
        goal_ids: goalIds,
        custom_times: customTimes,
      }),
    }, ReminderSyncResultSchema),
};

export const apiClient = api;
