"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Zap,
  Workflow,
  GitBranch,
  Store,
  TrendingUp,
  BookOpen,
  Settings,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    label: "Dashboard",
    icon: Home,
    href: "/",
  },
  {
    label: "Agent Builder",
    icon: Zap,
    href: "/builder",
  },
  {
    label: "Workflow Studio",
    icon: Workflow,
    href: "/workflows",
  },
  {
    label: "Orchestration",
    icon: GitBranch,
    href: "/orchestration",
  },
  {
    label: "Marketplace",
    icon: Store,
    href: "/marketplace",
  },
  {
    label: "Analytics",
    icon: TrendingUp,
    href: "/analytics",
  },
  {
    label: "Learning",
    icon: BookOpen,
    href: "/learning",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-border bg-secondary p-6 overflow-y-auto hidden lg:block">
      <div className="mb-8">
        <h1 className="text-2xl font-bold gradient-text">AgentThat</h1>
        <p className="text-xs text-muted-foreground mt-1">Enterprise AI OS</p>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-4 py-3 transition-colors duration-200",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-white/5"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
              {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-6 left-6 right-6 pt-6 border-t border-border">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-4 py-3 text-foreground hover:bg-white/5 transition-colors duration-200"
        >
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </Link>
      </div>
    </aside>
  );
}
