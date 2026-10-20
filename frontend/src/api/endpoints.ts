// Typed endpoint functions built on the api client.

import { apiRequest, tokenStore } from "./client";
import type {
  AdminOut,
  DeviceCreate,
  DeviceCreateResponse,
  DeviceOut,
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
