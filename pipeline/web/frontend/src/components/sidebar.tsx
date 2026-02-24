"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, Play, Activity, Table2, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { StatusDot } from "@/components/status-dot";
import { usePipelineStatus } from "@/lib/hooks";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/run", label: "Run Pipeline", icon: Play },
  { href: "/progress", label: "Progress", icon: Activity },
  { href: "/results", label: "Results", icon: Table2 },
  { href: "/logs", label: "Logs", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  const { state } = usePipelineStatus();
  const status = state?.status ?? "idle";

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card">
      {/* Header */}
      <div className="flex items-center gap-3 border-b px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Brain className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold">Hippocampus</p>
          <p className="text-xs text-muted-foreground">Feature Extraction</p>
        </div>
      </div>

      {/* Status */}
      <div className="border-b px-5 py-3">
        <div className="flex items-center gap-2">
          <StatusDot status={status} />
          <span className="text-xs font-medium capitalize">{status}</span>
          {status === "running" && (
            <Badge variant="secondary" className="ml-auto text-[10px] px-1.5">
              Batch {state?.progress.batch_num}/{state?.progress.total_batches}
            </Badge>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t px-5 py-3">
        <p className="text-[10px] text-muted-foreground">
          Pipeline Web UI &middot; Demo
        </p>
      </div>
    </aside>
  );
}
