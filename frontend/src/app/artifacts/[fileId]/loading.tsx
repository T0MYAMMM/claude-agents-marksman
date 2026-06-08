import { Skeleton } from "@/components/ui/skeleton";

export default function ArtifactLoading() {
  return (
    <>
      <div className="mb-6 space-y-4">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-48" />
      </div>
      <div className="grid gap-8 lg:grid-cols-[240px_1fr]">
        <div className="hidden space-y-2 lg:block">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
        <div className="space-y-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-4"
              style={{ width: `${70 + ((i * 13) % 30)}%` }}
            />
          ))}
        </div>
      </div>
    </>
  );
}
