import { CreateUrlPayload, ShortUrl } from "./types";

const API_BASE = "";

export async function createShortUrl(payload: CreateUrlPayload): Promise<ShortUrl> {
  const response = await fetch(`${API_BASE}/api/v1/urls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return response.json();
}
