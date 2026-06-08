"use client";

import { useTransition } from "react";
import { Check, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { approveAction } from "@/app/sessions/[id]/actions";
import { Button } from "@/components/ui/button";

/** Approve-plan button; disabled unless the session is awaiting review. */
export function ApproveButton({
  sessionId,
  enabled,
}: {
  sessionId: string;
  enabled: boolean;
}) {
  const [pending, startTransition] = useTransition();

  function onApprove() {
    startTransition(async () => {
      await approveAction(sessionId);
      toast.success("Plan approved");
    });
  }

  return (
    <Button
      type="button"
      variant="brand"
      disabled={!enabled || pending}
      onClick={onApprove}
    >
      {pending ? (
        <>
          <Loader2 className="size-4 animate-spin" /> Approving…
        </>
      ) : (
        <>
          <Check className="size-4" /> Approve plan
        </>
      )}
    </Button>
  );
}
