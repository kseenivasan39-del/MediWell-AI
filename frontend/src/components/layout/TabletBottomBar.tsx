"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  CalendarCheck,
  BarChart3,
  MessageSquare,
  User,
} from "lucide-react";

interface TabNavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TAB_NAV_ITEMS: TabNavItem[] = [
  { label: "Home", href: "/", icon: Home },
  { label: "Plan", href: "/wellness-plan", icon: CalendarCheck },
  { label: "Progress", href: "/analytics", icon: BarChart3 },
  { label: "Coach", href: "/coach", icon: MessageSquare },
  { label: "Profile", href: "/profile", icon: User },
];

export function TabletBottomBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Tablet bottom navigation"
      className="xl:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#0B1528] border-t border-slate-800/80 px-4 flex items-center justify-around z-40 shadow-lg select-none"
    >
      {TAB_NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-all ${
              isActive
                ? "text-teal-400 font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <div className={`p-1 rounded-md transition-colors ${isActive ? "bg-teal-500/15" : ""}`}>
              <Icon className={`w-5 h-5 ${isActive ? "text-teal-400 stroke-[2.2]" : "text-slate-400"}`} />
            </div>
            <span className={`text-[11px] mt-0.5 tracking-tight ${isActive ? "text-teal-300 font-medium" : "text-slate-400"}`}>
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
