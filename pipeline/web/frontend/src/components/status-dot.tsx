import { cn } from "@/lib/utils";

export function StatusDot({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-block h-2.5 w-2.5 rounded-full",
        status === "idle" && "bg-muted-foreground/40",
        status === "running" && "bg-emerald-500 animate-pulse",
        status === "completed" && "bg-emerald-500",
        status === "failed" && "bg-destructive",
        status === "cancelling" && "bg-amber-500 animate-pulse"
      )}
    />
  );
}
