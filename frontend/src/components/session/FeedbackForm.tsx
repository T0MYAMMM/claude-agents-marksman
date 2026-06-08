"use client";

import { useRef } from "react";
import { useFormStatus } from "react-dom";
import { Loader2, Send } from "lucide-react";
import { toast } from "sonner";

import { submitFeedbackAction } from "@/app/sessions/[id]/actions";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" variant="brand" disabled={pending}>
      {pending ? (
        <>
          <Loader2 className="size-4 animate-spin" /> Sending…
        </>
      ) : (
        <>
          <Send className="size-4" /> Send feedback
        </>
      )}
    </Button>
  );
}

/** Client form that injects reviewer feedback via a bound server action. */
export function FeedbackForm({ sessionId }: { sessionId: string }) {
  const formRef = useRef<HTMLFormElement>(null);

  async function action(formData: FormData) {
    await submitFeedbackAction(sessionId, formData);
    formRef.current?.reset();
    toast.success("Feedback sent");
  }

  return (
    <form ref={formRef} action={action} className="space-y-3">
      <Textarea
        name="comment"
        rows={3}
        required
        placeholder="Request a revision to the plan…"
      />
      <SubmitButton />
    </form>
  );
}
