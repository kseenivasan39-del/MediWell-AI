"use client";

import React, { useState, useEffect } from "react";
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Clock,
  ShieldCheck,
  Unlink,
  Bell,
  Sparkles,
} from "lucide-react";
import {
  apiClient,
  CalendarStatusResponse,
  ReminderSyncResult,
} from "@/lib/api";
import { DailyGoal } from "@/types/wellness";

interface CalendarIntegrationCardProps {
  patientId: string;
  patientName: string;
  goals: DailyGoal[];
}

export function CalendarIntegrationCard({
  patientId,
  patientName,
  goals,
}: CalendarIntegrationCardProps) {
  const [status, setStatus] = useState<CalendarStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isDisconnecting, setIsDisconnecting] = useState<boolean>(false);
  const [syncResult, setSyncResult] = useState<ReminderSyncResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Time overrides for goals (e.g. hydration or custom times)
  const [customTimes, setCustomTimes] = useState<Record<string, string>>({});

  const fetchStatus = async () => {
    try {
      setErrorMsg(null);
      const res = await apiClient.getCalendarStatus();
      setStatus(res);
    } catch (err: any) {
      console.error("Failed to load calendar status:", err);
      setErrorMsg(err.message || "Failed to load calendar connection status");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Check if URL has calendar_status query params from OAuth callback
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const calStatus = urlParams.get("calendar_status");
      const autoSyncedStr = urlParams.get("auto_synced");
      if (calStatus === "connected") {
        fetchStatus();
        // If goals are loaded, trigger patient-specific reminder sync immediately
        const numericGoalIds = goals
          .map((g) => parseInt(g.id, 10))
          .filter((id) => !isNaN(id));

        setIsSyncing(true);
        apiClient
          .syncCalendarReminders(patientId, numericGoalIds.length > 0 ? numericGoalIds : undefined)
          .then((res) => {
            setSyncResult(res);
            fetchStatus();
          })
          .catch((err) => {
            console.warn("Auto-sync follow-up:", err);
          })
          .finally(() => {
            setIsSyncing(false);
          });

        // Clean URL cleanly without reload
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
      } else if (calStatus === "error") {
        const msg = urlParams.get("message") || "Authorization failed.";
        setErrorMsg(`Google OAuth Error: ${msg}`);
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
      }
    }
  }, []);

  const handleConnect = async () => {
    try {
      setErrorMsg(null);
      const res = await apiClient.getCalendarConnectUrl();
      if (res.auth_url) {
        window.location.href = res.auth_url;
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not generate authorization URL");
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect this Google Calendar demo account?")) {
      return;
    }
    setIsDisconnecting(true);
    setErrorMsg(null);
    try {
      await apiClient.disconnectCalendar();
      setSyncResult(null);
      await fetchStatus();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to disconnect calendar");
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleSyncReminders = async () => {
    setIsSyncing(true);
    setErrorMsg(null);
    try {
      const numericCustomTimes: Record<number, string> = {};
      Object.entries(customTimes).forEach(([gid, val]) => {
        const num = parseInt(gid, 10);
        if (!isNaN(num) && val) {
          numericCustomTimes[num] = val;
        }
      });

      const goalIds = goals
        .map((g) => parseInt(g.id, 10))
        .filter((id) => !isNaN(id));

      const res = await apiClient.syncCalendarReminders(
        patientId,
        goalIds.length > 0 ? goalIds : undefined,
        numericCustomTimes
      );
      setSyncResult(res);
      await fetchStatus();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to sync calendar reminders");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCustomTimeChange = (goalId: string, val: string) => {
    setCustomTimes((prev) => ({ ...prev, [goalId]: val }));
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400">
            <CalendarIcon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Google Calendar Reminders
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                Direct OAuth 2.0
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Sync scheduled wellness goals as live calendar reminders into your primary Google Calendar.
            </p>
          </div>
        </div>

        {/* Status Pill & Action */}
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          {isLoading ? (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Checking...
            </div>
          ) : status?.is_connected ? (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                Connected
              </span>
              <button
                onClick={handleDisconnect}
                disabled={isDisconnecting}
                title="Disconnect Google Calendar"
                className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <Unlink className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
              Disconnected
            </span>
          )}
        </div>
      </div>

      {/* Account Confirmation & Details */}
      {status?.is_connected && (
        <div className="mt-4 p-3.5 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-1">
            <div className="text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              <span>
                Authorized Account: <strong className="text-slate-900 dark:text-slate-100">{status.account_email || "Connected"}</strong>
              </span>
            </div>
            <div className="text-slate-500 dark:text-slate-400 pl-6">
              Primary Calendar • Timezone: {status.timezone} • {status.synced_events_count} mapped events
            </div>
          </div>
          {status.last_synced_at && (
            <div className="text-slate-500 text-right shrink-0">
              Last synced: {new Date(status.last_synced_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
          )}
        </div>
      )}

      {/* Unconfigured Alert */}
      {!isLoading && !status?.is_configured && (
        <div className="mt-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-xs text-amber-800 dark:text-amber-300 space-y-1">
          <div className="flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            Google Calendar OAuth credentials not detected in backend/.env
          </div>
          <p className="text-amber-700 dark:text-amber-400/90 pl-6">
            To connect your live account, configure <code className="font-mono text-xs">GOOGLE_CLIENT_ID</code> and{" "}
            <code className="font-mono text-xs">GOOGLE_CLIENT_SECRET</code> in the backend environment.
          </p>
        </div>
      )}

      {/* Error Banner */}
      {errorMsg && (
        <div className="mt-4 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-xs text-rose-700 dark:text-rose-400 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Goal Preview & Sync Area */}
      <div className="mt-5 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Selected Goals for {patientName} ({goals.length})
          </h4>
          <span className="text-xs text-slate-500">Prefix: &ldquo;MediWell AI — ...&rdquo;</span>
        </div>

        {/* Goal Schedule List */}
        <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
          {goals.map((goal) => {
            const hasSchedule = Boolean(
              goal.recommendedTime &&
              !["Throughout day", "Mealtimes", "Anytime", "Daily"].includes(goal.recommendedTime)
            );
            const customVal = customTimes[goal.id] || "";

            return (
              <div
                key={goal.id}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs"
              >
                <div className="min-w-0 pr-3">
                  <div className="font-medium text-slate-800 dark:text-slate-200 truncate">{goal.title}</div>
                  <div className="text-slate-500 text-[11px] flex items-center gap-2 mt-0.5">
                    <span className="capitalize">{goal.category}</span>
                    <span>•</span>
                    <span className="capitalize">{goal.priority} priority</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {hasSchedule ? (
                    <span className="px-2 py-0.5 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 font-medium text-slate-700 dark:text-slate-200">
                      {goal.recommendedTime}
                    </span>
                  ) : (
                    <div className="flex items-center gap-1.5">
                      <input
                        type="text"
                        placeholder="e.g. 10:00 AM"
                        value={customVal}
                        onChange={(e) => handleCustomTimeChange(goal.id, e.target.value)}
                        className="w-24 px-2 py-1 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-800 dark:text-slate-200 text-xs focus:ring-1 focus:ring-teal-500 outline-none"
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Sync / Connect Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3">
          {status?.is_connected ? (
            <button
              onClick={handleSyncReminders}
              disabled={isSyncing}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-xs shadow-sm transition-colors disabled:opacity-50"
            >
              {isSyncing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Syncing Reminders...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Sync Reminders to Google Calendar
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleConnect}
              disabled={isLoading || !status?.is_configured}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-teal-600 dark:hover:bg-teal-500 font-medium text-xs shadow-sm transition-colors disabled:opacity-50"
            >
              <CalendarIcon className="w-4 h-4" />
              Connect Google Calendar
            </button>
          )}

          <div className="text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1.5 text-center sm:text-right">
            <Bell className="w-3.5 h-3.5 shrink-0" />
            10-minute popup reminder override enabled
          </div>
        </div>

        {/* Sync Success / Result Panel */}
        {syncResult && (
          <div className="p-4 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/60 text-xs space-y-2">
            <div className="flex items-center justify-between text-emerald-800 dark:text-emerald-300 font-semibold">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                Sync Complete ({syncResult.synced_count} events confirmed on Google Calendar)
              </span>
              {syncResult.skipped_count > 0 && (
                <span className="text-[11px] font-normal text-slate-500">
                  {syncResult.skipped_count} untimed habit(s) skipped
                </span>
              )}
            </div>

            {/* Event list */}
            {syncResult.events.length > 0 && (
              <div className="space-y-1.5 pt-1">
                {syncResult.events.map((evt) => (
                  <div
                    key={evt.google_event_id}
                    className="flex items-center justify-between py-1 px-2 rounded bg-white/70 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300"
                  >
                    <span className="truncate">{evt.title} ({evt.scheduled_time})</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] uppercase font-bold text-teal-600 dark:text-teal-400">
                        {evt.action}
                      </span>
                      {evt.html_link && (
                        <a
                          href={evt.html_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-teal-600 hover:text-teal-700"
                          title="Open in Google Calendar"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Notification Delivery Disclaimer */}
            <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1 border-t border-emerald-100 dark:border-emerald-900/40">
              {syncResult.delivery_notice}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
