import { HabitLog, DailyGoal, DriftAlert } from "@/types/wellness";

/**
 * Calculates current adherence percentage from habit logs.
 * Returns null if no habit logs exist.
 */
export function calculateAdherenceRate(logs: HabitLog[]): number | null {
  if (!logs || logs.length === 0) return null;
  const completed = logs.filter((log) => log.achieved).length;
  return Math.round((completed / logs.length) * 100);
}

/**
 * Counts completed and total daily goals.
 */
export function calculateGoalStats(goals: DailyGoal[]): {
  total: number;
  completed: number;
  remaining: number;
  percentage: number;
} {
  const total = goals.length;
  if (total === 0) {
    return { total: 0, completed: 0, remaining: 0, percentage: 0 };
  }
  const completed = goals.filter((g) => g.completed).length;
  const remaining = total - completed;
  const percentage = Math.round((completed / total) * 100);
  return { total, completed, remaining, percentage };
}

/**
 * Evaluates whether habit adherence meets drift conditions.
 * Rule: Drift is flagged only if recent 7-day adherence is at least 15% lower than previous 14-day baseline.
 */
export function evaluateDriftRule(
  previousAdherence: number,
  recentAdherence: number,
  thresholdPercentage = 15
): { isDrift: boolean; decline: number } {
  const decline = previousAdherence - recentAdherence;
  return {
    isDrift: decline >= thresholdPercentage,
    decline: Math.max(0, Math.round(decline)),
  };
}

/**
 * Formats date into readable string without timezone shifting.
 */
export function formatFriendlyDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}
