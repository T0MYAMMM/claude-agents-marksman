"use server";

import { revalidatePath } from "next/cache";
import { api } from "@/lib/api-client";

/** Submit reviewer feedback for a session, then refresh the page data. */
export async function submitFeedbackAction(sessionId: string, formData: FormData) {
  const comment = String(formData.get("comment") ?? "").trim();
  if (!comment) return;
  await api.submitFeedback(sessionId, comment);
  revalidatePath(`/sessions/${sessionId}`);
}

/** Approve a session's plan, moving it to EXECUTING. */
export async function approveAction(sessionId: string) {
  await api.approve(sessionId);
  revalidatePath(`/sessions/${sessionId}`);
}
