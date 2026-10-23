"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type ContrastMode = "normal" | "high" | "invert";
export type TextSizeMode = "normal" | "increase" | "decrease";

interface AccessibilityState {
  contrast: ContrastMode;
  saturation: boolean; // desaturate / grayscale
  highlightLinks: boolean;
  textSize: TextSizeMode;
  textSpacing: boolean;
  lineHeight: boolean;
  bigCursor: boolean;
  hideImages: boolean;
}

interface AccessibilityContextType {
  state: AccessibilityState;
  setContrast: (mode: ContrastMode) => void;
  toggleSaturation: () => void;
  toggleHighlightLinks: () => void;
  setTextSize: (mode: TextSizeMode) => void;
  toggleTextSpacing: () => void;
  toggleLineHeight: () => void;
  toggleBigCursor: () => void;
  toggleHideImages: () => void;
  resetAll: () => void;
}

const defaultState: AccessibilityState = {
  contrast: "normal",
  saturation: false,
  highlightLinks: false,
  textSize: "normal",
  textSpacing: false,
  lineHeight: false,
  bigCursor: false,
  hideImages: false,
};

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AccessibilityState>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("mediwell_accessibility");
        if (saved) return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to load accessibility settings", e);
      }
    }
    return defaultState;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("mediwell_accessibility", JSON.stringify(state));

    const html = document.documentElement;

    // Contrast
    html.classList.remove("a11y-high-contrast", "a11y-invert");
    if (state.contrast === "high") html.classList.add("a11y-high-contrast");
    if (state.contrast === "invert") html.classList.add("a11y-invert");

    // Saturation (Grayscale)
    if (state.saturation) html.classList.add("a11y-desaturate");
    else html.classList.remove("a11y-desaturate");

    // Highlight Links
    if (state.highlightLinks) html.classList.add("a11y-highlight-links");
    else html.classList.remove("a11y-highlight-links");

    // Text Size
    html.classList.remove("a11y-font-increase", "a11y-font-decrease");
    if (state.textSize === "increase") html.classList.add("a11y-font-increase");
    if (state.textSize === "decrease") html.classList.add("a11y-font-decrease");

    // Text Spacing
    if (state.textSpacing) html.classList.add("a11y-text-spacing");
    else html.classList.remove("a11y-text-spacing");

    // Line Height
    if (state.lineHeight) html.classList.add("a11y-line-height");
    else html.classList.remove("a11y-line-height");

    // Big Cursor
    if (state.bigCursor) html.classList.add("a11y-big-cursor");
    else html.classList.remove("a11y-big-cursor");

    // Hide Images
    if (state.hideImages) html.classList.add("a11y-hide-images");
    else html.classList.remove("a11y-hide-images");
  }, [state]);

  const setContrast = (mode: ContrastMode) => {
    setState((prev) => ({ ...prev, contrast: mode }));
  };

  const toggleSaturation = () => {
    setState((prev) => ({ ...prev, saturation: !prev.saturation }));
  };

  const toggleHighlightLinks = () => {
    setState((prev) => ({ ...prev, highlightLinks: !prev.highlightLinks }));
  };

  const setTextSize = (mode: TextSizeMode) => {
    setState((prev) => ({ ...prev, textSize: mode }));
  };

  const toggleTextSpacing = () => {
    setState((prev) => ({ ...prev, textSpacing: !prev.textSpacing }));
  };

  const toggleLineHeight = () => {
    setState((prev) => ({ ...prev, lineHeight: !prev.lineHeight }));
  };

  const toggleBigCursor = () => {
    setState((prev) => ({ ...prev, bigCursor: !prev.bigCursor }));
  };

  const toggleHideImages = () => {
    setState((prev) => ({ ...prev, hideImages: !prev.hideImages }));
  };

  const resetAll = () => {
    setState(defaultState);
  };

  return (
    <AccessibilityContext.Provider
      value={{
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
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error("useAccessibility must be used within an AccessibilityProvider");
  }
  return context;
}
