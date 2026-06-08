import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProjectLoading() {
  return (
    <>
      <div className="mb-6 space-y-4">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-4 w-80" />
      </div>
      <Skeleton className="mb-3 h-3 w-20" />
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="flex-row items-center gap-4 py-4">
            <div className="flex-1 space-y-2 px-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-3 w-40" />
            </div>
            <Skeleton className="h-2 w-40 px-2" />
          </Card>
        ))}
      </div>
    </>
  );
}
