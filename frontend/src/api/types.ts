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

export interface MetaInfo {
  server_version: string;
  latest_agent_version: string;
}

export interface ScreenshotPolicy {
  enabled: boolean;
  interval_minutes: number;
  active_hour_start: number | null;
  active_hour_end: number | null;
  retention_days: number;
  excluded_apps: string | null;
}

export interface ScreenshotMeta {
  id: number;
  captured_at: string;
  trigger: string;
  session_id: number | null;
  foreground_app: string | null;
  width: number;
  height: number;
  size_bytes: number;
}

export interface RemoteSession {
  id: number;
  status: string;
  initiated_by_email: string | null;
  started_at: string;
  ended_at: string | null;
  end_reason: string | null;
}

export interface AndroidStatus {
  configured: boolean;
  project_id: string | null;
  enterprise_name: string | null;
  capabilities: Record<string, boolean | string>;
  commands: string[];
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
