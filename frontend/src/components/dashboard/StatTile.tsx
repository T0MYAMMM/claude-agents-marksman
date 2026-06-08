import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

interface StatTileProps {
  label: string;
  value: number;
  icon: LucideIcon;
}

/** A metric tile: big number, muted label, accented lucide icon. */
export function StatTile({ label, value, icon: Icon }: StatTileProps) {
  return (
    <Card className="card-lift py-5">
      <CardContent className="flex items-center justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="font-display text-3xl leading-none tabular-nums">
            {value.toLocaleString()}
          </p>
        </div>
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
          <Icon className="size-5" />
        </span>
      </CardContent>
    </Card>
  );
}
