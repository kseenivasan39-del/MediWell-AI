import React from "react";
import { AlertCircle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  retry?: () => void;
}

export function ErrorState({
  title = "Unable to load data",
  message,
  retry,
}: ErrorStateProps) {
  return (
    <div className="p-8 rounded-xl bg-white border border-rose-200 text-center flex flex-col items-center justify-center space-y-3 shadow-xs">
      <div className="w-10 h-10 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
        <AlertCircle className="w-5 h-5" />
      </div>
      <div>
        <h4 className="text-sm font-bold text-slate-900">{title}</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">{message}</p>
      </div>
      {retry && (
        <button
          onClick={retry}
          type="button"
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition-colors"
        >
          Retry Request
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ComponentType<{ className?: string }>;
}

export function EmptyState({
  title,
  description,
  actionText,
  onAction,
  icon: Icon,
}: EmptyStateProps) {
  return (
    <div className="p-8 rounded-xl bg-white border border-slate-200 text-center flex flex-col items-center justify-center space-y-3">
      {Icon && (
        <div className="w-10 h-10 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400">
          <Icon className="w-5 h-5" />
        </div>
      )}
      <div>
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <p className="text-xs text-slate-500 max-w-md mt-1">{description}</p>
      </div>
      {actionText && onAction && (
        <button
          onClick={onAction}
          type="button"
          className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 font-medium hover:bg-slate-100 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

export function LoadingState({ message = "Loading wellness data..." }: { message?: string }) {
  return (
    <div className="p-12 rounded-xl bg-white border border-slate-200 flex flex-col items-center justify-center space-y-3">
      <div className="w-8 h-8 rounded-full border-2 border-teal-500 border-t-transparent animate-spin" />
      <span className="text-xs text-slate-500 font-medium">{message}</span>
    </div>
  );
}
