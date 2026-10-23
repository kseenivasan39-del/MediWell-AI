"use client";

import React from "react";
import { DesktopSidebar } from "./DesktopSidebar";
import { DesktopHeader } from "./DesktopHeader";
import { TabletBottomBar } from "./TabletBottomBar";

interface DesktopLayoutProps {
  children: React.ReactNode;
  pageTitle: string;
  breadcrumb?: string;
}

export function DesktopLayout({
  children,
  pageTitle,
  breadcrumb = "Overview",
}: DesktopLayoutProps) {
  const [isOpenMobile, setIsOpenMobile] = React.useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans">
      {/* Desktop Fixed Left Sidebar (hidden on tablet/1024px: xl:flex only) */}
      <div className="hidden xl:flex">
        <DesktopSidebar
          isOpenMobile={isOpenMobile}
          onCloseMobile={() => setIsOpenMobile(false)}
        />
      </div>

      {/* Main Content Workspace */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        <DesktopHeader
          pageTitle={pageTitle}
          breadcrumb={breadcrumb}
          onMenuClick={() => setIsOpenMobile(!isOpenMobile)}
        />

        {/* Scrollable Canvas with bottom spacing for tablet bottom bar */}
        <main className="flex-1 overflow-y-auto px-4 md:px-6 lg:px-8 py-5 pb-20 xl:pb-6">
          <div className="max-w-7xl mx-auto space-y-5">
            {children}
          </div>
        </main>

        {/* Tablet / Mobile Bottom Navigation Bar */}
        <TabletBottomBar />
      </div>
    </div>
  );
}
