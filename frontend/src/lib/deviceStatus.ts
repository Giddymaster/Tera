// Derives a device's live status from its enrollment state and last check-in.
// A device is only "online" when its last check-in is recent — a stale or
// missing check-in never counts as online.

import type { DeviceOut } from "../api/types";

// How recent a check-in must be to count as "online".
export const ONLINE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

export type LiveStatus = "online" | "offline" | "pending" | "revoked";

export function computeStatus(device: DeviceOut, now: number = Date.now()): LiveStatus {
  if (device.enrollment_status === "revoked") return "revoked";
  if (device.enrollment_status === "pending" || !device.last_seen_at) return "pending";
  const lastSeen = new Date(device.last_seen_at).getTime();
  if (Number.isNaN(lastSeen)) return "pending";
  return now - lastSeen <= ONLINE_THRESHOLD_MS ? "online" : "offline";
}

export const STATUS_LABEL: Record<LiveStatus, string> = {
  online: "Online",
  offline: "Offline",
  pending: "Awaiting check-in",
  revoked: "Revoked",
};
