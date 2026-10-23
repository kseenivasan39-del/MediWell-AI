import { z } from "zod";

export const HabitLogSchema = z.object({
  id: z.string(),
  date: z.string(), // ISO date YYYY-MM-DD
  habitName: z.string(),
  category: z.enum(["nutrition", "hydration", "activity", "sleep", "mindfulness", "medication"]),
  target: z.string(),
  achieved: z.boolean(),
  notes: z.string().optional(),
});

export type HabitLog = z.infer<typeof HabitLogSchema>;

export const DailyGoalSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  category: z.enum(["nutrition", "hydration", "activity", "sleep", "mindfulness", "medication"]),
  completed: z.boolean(),
  priority: z.enum(["low", "medium", "high"]),
  recommendedTime: z.string().optional(),
});

export type DailyGoal = z.infer<typeof DailyGoalSchema>;

export const ConditionSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  severity: z.enum(["Mild", "Moderate", "Managed", "Under Review"]),
  diagnosedDate: z.string(),
  notes: z.string(),
});

export type Condition = z.infer<typeof ConditionSchema>;

export const DriftAlertSchema = z.object({
  hasDrift: z.boolean(),
  declinePercentage: z.number(), // e.g. 18.5%
  previousPeriod: z.string(), // e.g. "Last 14 days"
  previousAdherence: z.number(), // e.g. 84
  recentPeriod: z.string(), // e.g. "Past 7 days"
  recentAdherence: z.number(), // e.g. 62
  primaryLaggingHabits: z.array(z.string()),
  reason: z.string(),
  recoverySuggestion: z.string(),
  thresholdMet: z.boolean(),
});

export type DriftAlert = z.infer<typeof DriftAlertSchema>;

export const AIInsightSchema = z.object({
  id: z.string(),
  category: z.enum(["Clinical Preventive", "Hydration Balance", "Activity Modification", "Nutritional Timing"]),
  title: z.string(),
  observation: z.string(),
  actionableRecommendation: z.string(),
  evidenceBasis: z.string(),
  confidence: z.number(), // e.g. 0.92
  isVerified: z.boolean(),
  generatedAt: z.string(),
});

export type AIInsight = z.infer<typeof AIInsightSchema>;

export const SyntheticPatientSchema = z.object({
  id: z.string(),
  demoIdentifier: z.string(),
  name: z.string(),
  age: z.number(),
  gender: z.string(),
  avatarUrl: z.string().optional(),
  primaryCondition: ConditionSchema,
  secondaryConditions: z.array(ConditionSchema),
  profileCompleteness: z.number(), // percentage 0-100
  dataQualityRating: z.enum(["High Quality", "Moderate", "Sparse", "Pending Verification"]),
  activePlanName: z.string(),
  planStatus: z.enum(["Active", "Under Review", "Paused", "Optimized"]),
  goals: z.array(DailyGoalSchema),
  recentHabitLogs: z.array(HabitLogSchema),
  weeklyAdherenceHistory: z.array(
    z.object({
      weekLabel: z.string(),
      adherenceRate: z.number(),
      targetRate: z.number(),
      activeHabits: z.number(),
    })
  ),
  dailyAdherenceTrend: z.array(
    z.object({
      day: z.string(),
      adherence: z.number(),
      hydration: z.number(),
      activity: z.number(),
      nutrition: z.number(),
    })
  ),
  driftAlert: DriftAlertSchema.optional(),
  aiInsights: z.array(AIInsightSchema),
  lastSyncedAt: z.string(),
});

export type SyntheticPatient = z.infer<typeof SyntheticPatientSchema>;
