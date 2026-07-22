import type { ChatApiResponse } from "@/lib/types";

export async function sendChatMessage(message: string, sessionId?: string): Promise<ChatApiResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId ?? null }),
  });

  const data = await res.json();

  if (!res.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : data?.error ?? "Something went wrong.";
    throw new Error(detail);
  }

  return data as ChatApiResponse;
}
