"use server";

import { api } from "@/lib/api-client";
import type { ChatMessage } from "@/types";

/** Proxy a chat turn to the backend assistant (keeps the API server-side). */
export async function chatAction(
  fileId: string,
  messages: ChatMessage[],
  currentMarkdown: string,
) {
  return api.chatArtifact(fileId, messages, currentMarkdown);
}

/** Save edited Markdown back to Google Drive via the backend. */
export async function saveArtifactAction(fileId: string, content: string) {
  return api.updateArtifact(fileId, content);
}
