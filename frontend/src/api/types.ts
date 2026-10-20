// TypeScript types mirroring the backend API schemas.

export type Role = "owner" | "admin" | "viewer";
export type OSType = "windows" | "android" | "ios";
export type DeviceType = "laptop" | "phone" | "tablet";
export type EnrollmentStatus = "pending" | "enrolled" | "revoked";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AdminOut {
  id: number;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
  permissions: string[];
}

export interface DeviceOut {
  id: number;
  device_uid: string;
  name: string;
  os_type: OSType;
  device_type: DeviceType;
  assigned_to: string | null;
  enrollment_status: EnrollmentStatus;
  created_at: string;
  updated_at: string;
  last_seen_at: string | null;
  agent_version: string | null;
  os_version: string | null;
  disk_free_gb: number | null;
  disk_total_gb: number | null;
  battery_percent: number | null;
  power_plugged: boolean | null;
}

export interface AppUsageOut {
  app_name: string;
  seconds: number;
}

export interface DeviceUsageOut {
  device_uid: string;
  days: number;
  total_seconds: number;
  apps: AppUsageOut[];
}

export interface AuditLogOut {
  id: number;
  timestamp: string;
  actor_email: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  detail: string | null;
  ip_address: string | null;
}

export interface DeviceCreate {
  name: string;
  os_type: OSType;
  device_type: DeviceType;
  assigned_to?: string | null;
}

export interface DeviceCreateResponse {
  device: DeviceOut;
  enrollment_secret: string;
}
