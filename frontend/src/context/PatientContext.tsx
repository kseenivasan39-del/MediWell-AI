"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { SyntheticPatient } from "@/types/wellness";
import { SYNTHETIC_PATIENTS } from "@/data/synthetic-patients";
import { api, DashboardResponse, PatientListItem, RecoveryProposal } from "@/lib/api";
import { mapBackendToSyntheticPatient } from "@/lib/patient-adapter";

interface PatientContextType {
  patients: SyntheticPatient[];
  selectedPatient: SyntheticPatient;
  backendDashboard: DashboardResponse | null;
  recoveryProposals: RecoveryProposal[];
  setSelectedPatientId: (id: string) => void;
  toggleGoalCompletion: (goalId: string) => Promise<void>;
  createRecoveryProposal: (notes?: string) => Promise<RecoveryProposal | null>;
  submitRecoveryDecision: (proposalId: number, decision: "accepted" | "edited" | "rejected", notes?: string, revisedTargets?: any[]) => Promise<void>;
  isLoading: boolean;
  isSyncing: boolean;
  error: string | null;
  refreshPatientData: () => Promise<void>;
}

const PatientContext = createContext<PatientContextType | undefined>(undefined);

export function PatientProvider({ children }: { children: React.ReactNode }) {
  const [patients, setPatients] = useState<SyntheticPatient[]>(SYNTHETIC_PATIENTS);
  const [selectedPatientId, setSelectedPatientIdState] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("mediwell_selected_patient");
      if (saved) return saved;
    }
    return "SYNTH-T2D-8841"; // Default to Eleanor Vance synthetic code
  });

  const [backendDashboard, setBackendDashboard] = useState<DashboardResponse | null>(null);
  const [recoveryProposals, setRecoveryProposals] = useState<RecoveryProposal[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Initial Load: Fetch patient list from backend or fall back safely
  useEffect(() => {
    let mounted = true;
    async function loadPatients() {
      try {
        const backendPatients = await api.getPatients();
        if (mounted && backendPatients && backendPatients.length > 0) {
          // Convert patient list into synthetic patient stubs
          const mapped = backendPatients.map((bp) => {
            const fallbackMatch = SYNTHETIC_PATIENTS.find((p) => p.demoIdentifier === bp.synthetic_identifier);
            if (fallbackMatch) {
              return {
                ...fallbackMatch,
                id: bp.synthetic_identifier,
                name: bp.display_name,
                demoIdentifier: bp.synthetic_identifier,
              };
            }
            return {
              id: bp.synthetic_identifier,
              demoIdentifier: bp.synthetic_identifier,
              name: bp.display_name,
              age: bp.age,
              gender: bp.gender,
              primaryCondition: {
                id: `cond-${bp.id}`,
                name: bp.primary_condition,
                category: "Preventive",
                severity: bp.condition_severity as any,
                diagnosedDate: "2024-01-01",
                notes: "",
              },
              secondaryConditions: [],
              profileCompleteness: bp.profile_completeness,
              dataQualityRating: (["High Quality", "Moderate", "Sparse", "Pending Verification"].includes(bp.data_quality_rating) ? bp.data_quality_rating : "Moderate") as any,
              activePlanName: bp.active_plan_name || "No Plan Prescribed",
              planStatus: "Active" as const,
              goals: [],
              recentHabitLogs: [],
              weeklyAdherenceHistory: [],
              dailyAdherenceTrend: [],
              aiInsights: [],
              lastSyncedAt: "Connected to Backend",
            };
          });
          setPatients(mapped);
        }
      } catch (err: any) {
        console.warn("[PatientProvider] Backend patient list unavailable; using synthetic presets.", err);
      }
    }
    loadPatients();
    return () => {
      mounted = false;
    };
  }, []);

  // 2. Fetch Dashboard & Telemetry for Selected Patient
  const loadPatientDashboard = useCallback(async (patientIdentifier: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [dash, trends, proposals] = await Promise.allSettled([
        api.getPatientDashboard(patientIdentifier),
        api.getTrends(patientIdentifier, 14),
        api.getRecoveryProposals(patientIdentifier),
      ]);

      if (dash.status === "fulfilled") {
        const dashboardData = dash.value;
        const trendsData = trends.status === "fulfilled" ? trends.value : null;
        const mappedPatient = mapBackendToSyntheticPatient(dashboardData, trendsData);

        setBackendDashboard(dashboardData);
        setPatients((prev) => {
          const index = prev.findIndex((p) => p.id === patientIdentifier || p.demoIdentifier === patientIdentifier);
          if (index >= 0) {
            const copy = [...prev];
            copy[index] = mappedPatient;
            return copy;
          }
          return [...prev, mappedPatient];
        });

        if (proposals.status === "fulfilled") {
          setRecoveryProposals(proposals.value);
        }
      } else {
        throw dash.reason;
      }
    } catch (err: any) {
      console.warn(`[PatientProvider] Failed to load dashboard from API for ${patientIdentifier}; falling back.`, err);
      setError(`Notice: Using local synthetic profile for ${patientIdentifier} (${err?.message || "Backend offline"})`);
      // Keep selected patient from fallback SYNTHETIC_PATIENTS
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPatientDashboard(selectedPatientId);
  }, [selectedPatientId, loadPatientDashboard]);

  const setSelectedPatientId = (id: string) => {
    setSelectedPatientIdState(id);
    if (typeof window !== "undefined") {
      localStorage.setItem("mediwell_selected_patient", id);
    }
  };

  const selectedPatient =
    patients.find((p) => p.id === selectedPatientId || p.demoIdentifier === selectedPatientId) || patients[0];

  // 3. Real-time Habit Logging / Goal Completion
  const toggleGoalCompletion = async (goalId: string) => {
    setIsSyncing(true);
    const goalNumber = parseInt(goalId, 10);
    const todayItem = backendDashboard?.today_goals.items.find((g) => g.goal_id === goalNumber);

    // Optimistic UI update
    setPatients((prev) =>
      prev.map((patient) => {
        if (patient.id !== selectedPatientId && patient.demoIdentifier !== selectedPatientId) return patient;
        const updatedGoals = patient.goals.map((goal) => {
          if (goal.id === goalId) {
            return { ...goal, completed: !goal.completed };
          }
          return goal;
        });
        return { ...patient, goals: updatedGoals };
      })
    );

    try {
      if (todayItem && todayItem.today_log_id) {
        // Update existing log
        await api.updateHabitLog(todayItem.today_log_id, {
          is_completed: !todayItem.is_completed_today,
        });
      } else if (todayItem) {
        // Create new log
        const todayStr = new Date().toISOString().split("T")[0];
        await api.createHabitLog(selectedPatientId, {
          habit_id: todayItem.habit_id,
          log_date: todayStr,
          is_completed: true,
          numeric_value: todayItem.target_value || 1,
          notes: "Logged via MediWell AI Dashboard",
        });
      }
      // Reload dashboard telemetry to refresh adherence & momentum
      await loadPatientDashboard(selectedPatientId);
    } catch (err: any) {
      console.warn("[PatientProvider] Failed to persist goal toggle to backend:", err);
      // Still retain optimistic UI for demo continuity
    } finally {
      setIsSyncing(false);
    }
  };

  // 4. Recovery Proposal Actions
  const createRecoveryProposal = async (notes?: string) => {
    try {
      const prop = await api.createRecoveryProposal(selectedPatientId, notes);
      setRecoveryProposals((prev) => [prop, ...prev]);
      await loadPatientDashboard(selectedPatientId);
      return prop;
    } catch (err: any) {
      console.error("[PatientProvider] Error creating recovery proposal:", err);
      return null;
    }
  };

  const submitRecoveryDecision = async (
    proposalId: number,
    decision: "accepted" | "edited" | "rejected",
    notes?: string,
    revisedTargets?: any[]
  ) => {
    try {
      await api.submitRecoveryDecision(proposalId, decision, notes, revisedTargets);
      await loadPatientDashboard(selectedPatientId);
    } catch (err: any) {
      console.error("[PatientProvider] Error submitting recovery decision:", err);
      throw err;
    }
  };

  const refreshPatientData = async () => {
    await loadPatientDashboard(selectedPatientId);
  };

  return (
    <PatientContext.Provider
      value={{
        patients,
        selectedPatient,
        backendDashboard,
        recoveryProposals,
        setSelectedPatientId,
        toggleGoalCompletion,
        createRecoveryProposal,
        submitRecoveryDecision,
        isLoading,
        isSyncing,
        error,
        refreshPatientData,
      }}
    >
      {children}
    </PatientContext.Provider>
  );
}

export function usePatient() {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error("usePatient must be used within a PatientProvider");
  }
  return context;
}
