"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAccessibility } from "@/context/AccessibilityContext";
import {
  SunMedium,
  Check,
  Link as LinkIcon,
  Contrast,
  Droplet,
  ZoomIn,
  Type,
  ZoomOut,
  MoveHorizontal,
  AlignVerticalSpaceAround,
  MousePointer2,
  ImageOff,
  RotateCcw,
  Sparkles,
} from "lucide-react";

export function AccessibilityMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const {
    state,
    setContrast,
    toggleSaturation,
    toggleHighlightLinks,
    setTextSize,
    toggleTextSpacing,
    toggleLineHeight,
    toggleBigCursor,
    toggleHideImages,
    resetAll,
  } = useAccessibility();

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      {/* Top Header Accessibility Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Accessibility Tools"
        title="Accessibility Tools"
        className={`w-9 h-9 rounded-lg border flex items-center justify-center transition-all ${
          isOpen
            ? "bg-teal-50 border-teal-500 text-teal-700 shadow-xs"
            : "border-slate-200 bg-white text-slate-700 hover:text-slate-900 hover:bg-slate-50"
        }`}
      >
        {/* Universal Accessibility Icon */}
        <svg
          className="w-5 h-5 a11y-keep-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="4" r="1.5" />
          <path d="M12 7v7" />
          <path d="M6 9.5l6-1.5 6 1.5" />
          <path d="M9 20l3-6 3 6" />
        </svg>
      </button>

      {/* Accessibility Popover Modal */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-[340px] bg-white rounded-2xl shadow-2xl border border-slate-200 p-5 z-50 animate-in fade-in zoom-in-95 duration-150 text-slate-800">
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Accessibility Tools
            </h3>
            <button
              type="button"
              onClick={resetAll}
              className="text-[11px] font-medium text-slate-500 hover:text-teal-700 flex items-center gap-1 transition-colors px-1.5 py-0.5 rounded hover:bg-slate-50"
            >
              <RotateCcw className="w-3 h-3 a11y-keep-icon" />
              Reset
            </button>
          </div>

          {/* Section 1: Color Contrast */}
          <div className="space-y-2 mb-4">
            <span className="text-xs font-semibold text-slate-700 block">
              Color Contrast
            </span>
            <div className="grid grid-cols-3 gap-2">
              {/* High Contrast */}
              <button
                type="button"
                onClick={() =>
                  setContrast(state.contrast === "high" ? "normal" : "high")
                }
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.contrast === "high"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.contrast === "high" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <SunMedium className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  High Contrast
                </span>
              </button>

              {/* Normal Contrast */}
              <button
                type="button"
                onClick={() => setContrast("normal")}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.contrast === "normal"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.contrast === "normal" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <div className="w-3.5 h-3.5 rounded-xs border-2 border-current" />
                </div>
                <span className="text-[11px] font-medium leading-tight underline decoration-slate-300">
                  Normal Contrast
                </span>
              </button>

              {/* Highlight Links */}
              <button
                type="button"
                onClick={toggleHighlightLinks}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.highlightLinks
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.highlightLinks && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <LinkIcon className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Highlight Links
                </span>
              </button>

              {/* Invert */}
              <button
                type="button"
                onClick={() =>
                  setContrast(state.contrast === "invert" ? "normal" : "invert")
                }
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.contrast === "invert"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.contrast === "invert" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <Contrast className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Invert
                </span>
              </button>

              {/* Saturation (Desaturate) */}
              <button
                type="button"
                onClick={toggleSaturation}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.saturation
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.saturation && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <Droplet className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Saturation
                </span>
              </button>
            </div>
          </div>

          {/* Section 2: Text Size */}
          <div className="space-y-2 mb-4">
            <span className="text-xs font-semibold text-slate-700 block">
              Text Size
            </span>
            <div className="grid grid-cols-3 gap-2">
              {/* Font Size Increase */}
              <button
                type="button"
                onClick={() =>
                  setTextSize(state.textSize === "increase" ? "normal" : "increase")
                }
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.textSize === "increase"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.textSize === "increase" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <span className="text-base font-bold text-slate-900 mb-0.5">
                  A+
                </span>
                <span className="text-[11px] font-medium leading-tight underline decoration-slate-300">
                  Font Size Increase
                </span>
              </button>

              {/* Normal Font */}
              <button
                type="button"
                onClick={() => setTextSize("normal")}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.textSize === "normal"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.textSize === "normal" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <span className="text-base font-bold text-slate-900 mb-0.5">
                  A
                </span>
                <span className="text-[11px] font-medium leading-tight">
                  Normal Font
                </span>
              </button>

              {/* Font Size Decrease */}
              <button
                type="button"
                onClick={() =>
                  setTextSize(state.textSize === "decrease" ? "normal" : "decrease")
                }
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.textSize === "decrease"
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.textSize === "decrease" && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <span className="text-base font-bold text-slate-900 mb-0.5">
                  A-
                </span>
                <span className="text-[11px] font-medium leading-tight">
                  Font Size Decrease
                </span>
              </button>

              {/* Text Spacing */}
              <button
                type="button"
                onClick={toggleTextSpacing}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.textSpacing
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.textSpacing && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <MoveHorizontal className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Text Spacing
                </span>
              </button>

              {/* Line Height */}
              <button
                type="button"
                onClick={toggleLineHeight}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.lineHeight
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.lineHeight && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <AlignVerticalSpaceAround className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Line Height
                </span>
              </button>
            </div>
          </div>

          {/* Section 3: Other Controls */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-700 block">
              Other Controls
            </span>
            <div className="grid grid-cols-2 gap-2">
              {/* Big Cursor */}
              <button
                type="button"
                onClick={toggleBigCursor}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.bigCursor
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.bigCursor && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <MousePointer2 className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Big Cursor
                </span>
              </button>

              {/* Hide Image */}
              <button
                type="button"
                onClick={toggleHideImages}
                className={`relative p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  state.hideImages
                    ? "border-teal-600 bg-teal-50/60 text-teal-900 ring-2 ring-teal-500/20"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700"
                }`}
              >
                {state.hideImages && (
                  <span className="absolute top-1.5 right-1.5 w-3.5 h-3.5 rounded-full bg-teal-600 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 a11y-keep-icon stroke-[3]" />
                  </span>
                )}
                <div className="w-6 h-6 mb-1.5 flex items-center justify-center">
                  <ImageOff className="w-4 h-4 a11y-keep-icon" />
                </div>
                <span className="text-[11px] font-medium leading-tight">
                  Hide Image
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
