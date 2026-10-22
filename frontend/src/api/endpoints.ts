// Typed endpoint functions built on the api client.

import { apiBlob, apiRequest, tokenStore } from "./client";
import type {
  AdminOut,
  Alert,
  AndroidStatus,
  AppleStatus,
  AuditLogOut,
  DeviceCreate,
  DeviceCreateResponse,
  DeviceLocation,
  DeviceOut,
  DeviceUsageOut,
  MetaInfo,
  RemoteSession,
  ReportSummary,
  RustDeskInfo,
  ScreenshotMeta,
  ScreenshotPolicy,
  TokenResponse,
} from "./types";

export async function login(email: string, password: string): Promise<AdminOut> {
  const tokens = await apiRequest<TokenResponse>(
    "/auth/login",
    { method: "POST", body: { email, password }, auth: false },
  );
  tokenStore.set(tokens);
  return getMe();
}

export function getMe(): Promise<AdminOut> {
  return apiRequest<AdminOut>("/auth/me");
}

export function listDevices(): Promise<DeviceOut[]> {
  return apiRequest<DeviceOut[]>("/devices");
}

export function getDevice(deviceUid: string): Promise<DeviceOut> {
  return apiRequest<DeviceOut>(`/devices/${deviceUid}`);
}

export function createDevice(data: DeviceCreate): Promise<DeviceCreateResponse> {
  return apiRequest<DeviceCreateResponse>("/devices", { method: "POST", body: data });
}

export function revokeDevice(deviceUid: string): Promise<DeviceOut> {
  return apiRequest<DeviceOut>(`/devices/${deviceUid}/revoke`, { method: "POST" });
}

export function deleteDevice(deviceUid: string): Promise<void> {
  return apiRequest<void>(`/devices/${deviceUid}`, { method: "DELETE" });
}

export function listAuditLogs(limit = 100): Promise<AuditLogOut[]> {
  return apiRequest<AuditLogOut[]>(`/audit?limit=${limit}`);
}

export function getDeviceUsage(deviceUid: string, days = 7): Promise<DeviceUsageOut> {
  return apiRequest<DeviceUsageOut>(`/devices/${deviceUid}/usage?days=${days}`);
}

export function getMeta(): Promise<MetaInfo> {
  return apiRequest<MetaInfo>("/meta", { auth: false });
}

// ---- Screenshots ----
export function getScreenshotPolicy(uid: string): Promise<ScreenshotPolicy> {
  return apiRequest<ScreenshotPolicy>(`/devices/${uid}/screenshot-policy`);
}

export function updateScreenshotPolicy(
  uid: string,
  policy: ScreenshotPolicy,
): Promise<ScreenshotPolicy> {
  return apiRequest<ScreenshotPolicy>(`/devices/${uid}/screenshot-policy`, {
    method: "PUT",
    body: policy,
  });
}

export function requestCapture(uid: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/devices/${uid}/screenshots/request`, {
    method: "POST",
  });
}

export function listScreenshots(
  uid: string,
  limit = 50,
  offset = 0,
): Promise<ScreenshotMeta[]> {
  return apiRequest<ScreenshotMeta[]>(
    `/devices/${uid}/screenshots?limit=${limit}&offset=${offset}`,
  );
}

export function deleteScreenshot(id: number): Promise<void> {
  return apiRequest<void>(`/screenshots/${id}`, { method: "DELETE" });
}

export function deleteAllScreenshots(uid: string): Promise<void> {
  return apiRequest<void>(`/devices/${uid}/screenshots`, { method: "DELETE" });
}

export function getScreenshotImage(id: number): Promise<Blob> {
  return apiBlob(`/screenshots/${id}/image`);
}

// ---- Remote support sessions ----
export function startSession(uid: string): Promise<RemoteSession> {
  return apiRequest<RemoteSession>(`/devices/${uid}/sessions`, { method: "POST" });
}

export function listSessions(uid: string): Promise<RemoteSession[]> {
  return apiRequest<RemoteSession[]>(`/devices/${uid}/sessions`);
}

export function endSession(id: number): Promise<RemoteSession> {
  return apiRequest<RemoteSession>(`/sessions/${id}/end`, { method: "POST" });
}

export function getSessionScreenshots(id: number): Promise<ScreenshotMeta[]> {
  return apiRequest<ScreenshotMeta[]>(`/sessions/${id}/screenshots`);
}

// ---- Android management ----
export function getAndroidStatus(): Promise<AndroidStatus> {
  return apiRequest<AndroidStatus>("/android/status");
}

export function getAndroidDevices(): Promise<Record<string, unknown>[]> {
  return apiRequest<Record<string, unknown>[]>("/android/devices");
}

// ---- Apple MDM ----
export function getAppleStatus(): Promise<AppleStatus> {
  return apiRequest<AppleStatus>("/apple/status");
}

// ---- Location ----
export function getDeviceLocation(uid: string): Promise<DeviceLocation> {
  return apiRequest<DeviceLocation>(`/devices/${uid}/location`);
}

export function updateLocationPolicy(
  uid: string,
  body: { enabled: boolean; retention_days: number },
): Promise<{ enabled: boolean; retention_days: number }> {
  return apiRequest(`/devices/${uid}/location-policy`, { method: "PUT", body });
}

export function requestLocation(uid: string): Promise<{ status: string }> {
  return apiRequest(`/devices/${uid}/location/request`, { method: "POST" });
}

// ---- Alerts & reports ----
export function getAlerts(): Promise<Alert[]> {
  return apiRequest<Alert[]>("/alerts");
}

export function getReportSummary(): Promise<ReportSummary> {
  return apiRequest<ReportSummary>("/reports/summary");
}

// ---- RustDesk remote control ----
export function getRustDesk(uid: string): Promise<RustDeskInfo> {
  return apiRequest<RustDeskInfo>(`/devices/${uid}/rustdesk`);
}
