import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getDevice, getDeviceUsage, getMeta } from "../api/endpoints";
import type { DeviceOut, DeviceUsageOut, MetaInfo } from "../api/types";
import { RemoteSupportPanel } from "../components/RemoteSupportPanel";
import { ScreenshotsPanel } from "../components/ScreenshotsPanel";
import { StatusBadge } from "../components/StatusBadge";
import { computeStatus } from "../lib/deviceStatus";
import { formatDateTime, formatDuration, relativeTime } from "../lib/format";

const OS_LABEL: Record<string, string> = {
  windows: "Windows",
  android: "Android",
  ios: "iOS",
};

// Sections populated in later milestones.
const FUTURE_SECTIONS = [{ title: "Location", milestone: "Milestone 10" }];

function diskLabel(device: DeviceOut): string | null {
  if (device.disk_free_gb == null || device.disk_total_gb == null) return null;
  return `${device.disk_free_gb.toFixed(0)} GB free of ${device.disk_total_gb.toFixed(0)} GB`;
}

export function DeviceDetailPage() {
  const { deviceUid = "" } = useParams();
  const [device, setDevice] = useState<DeviceOut | null>(null);
  const [usage, setUsage] = useState<DeviceUsageOut | null>(null);
  const [meta, setMeta] = useState<MetaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [d, u, m] = await Promise.all([
          getDevice(deviceUid),
          getDeviceUsage(deviceUid, 7).catch(() => null),
          getMeta().catch(() => null),
        ]);
        if (active) {
          setDevice(d);
          setUsage(u);
          setMeta(m);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof ApiError && err.status === 404
              ? "This device was not found. It may have been deleted."
              : "Could not load this device.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [deviceUid]);

  if (loading) return <div className="centered muted">Loading device…</div>;
  if (error || !device) {
    return (
      <div className="page">
        <Link to="/" className="link-back">
          ← Back to devices
        </Link>
        <div className="alert alert-error">{error ?? "Device not found."}</div>
      </div>
    );
  }

  const disk = diskLabel(device);
  const diskUsedPct =
    device.disk_free_gb != null && device.disk_total_gb
      ? Math.round(
          ((device.disk_total_gb - device.disk_free_gb) / device.disk_total_gb) * 100,
        )
      : null;
  const maxUsage = usage?.apps.length ? usage.apps[0].seconds : 0;

  return (
    <div className="page">
      <Link to="/" className="link-back">
        ← Back to devices
      </Link>

      <div className="page-head">
        <div>
          <h1>{device.name}</h1>
          <p className="muted small mono">{device.device_uid}</p>
        </div>
        <StatusBadge status={computeStatus(device)} />
      </div>

      <section className="card">
        <h2 className="card-title">Device information</h2>
        <dl className="detail-grid">
          <div>
            <dt>Operating system</dt>
            <dd>{OS_LABEL[device.os_type] ?? device.os_type}</dd>
          </div>
          <div>
            <dt>Device type</dt>
            <dd className="cap">{device.device_type}</dd>
          </div>
          <div>
            <dt>Assigned to</dt>
            <dd>{device.assigned_to ?? "—"}</dd>
          </div>
          <div>
            <dt>Enrollment status</dt>
            <dd className="cap">{device.enrollment_status}</dd>
          </div>
          <div>
            <dt>Agent version</dt>
            <dd>
              {device.agent_version ?? "—"}
              {device.agent_version &&
                meta &&
                device.agent_version !== meta.latest_agent_version && (
                  <span className="update-badge" title={`Latest: ${meta.latest_agent_version}`}>
                    Update available
                  </span>
                )}
            </dd>
          </div>
          <div>
            <dt>OS version</dt>
            <dd>{device.os_version ?? "—"}</dd>
          </div>
          <div>
            <dt>Registered</dt>
            <dd>{formatDateTime(device.created_at)}</dd>
          </div>
          <div>
            <dt>Last check-in</dt>
            <dd>
              {formatDateTime(device.last_seen_at)}
              <span className="muted small"> ({relativeTime(device.last_seen_at)})</span>
            </dd>
          </div>
        </dl>
      </section>

      <section className="card">
        <h2 className="card-title">Health</h2>
        {disk == null && device.battery_percent == null ? (
          <p className="muted small">No health data reported yet.</p>
        ) : (
          <div className="health-grid">
            {disk != null && (
              <div>
                <div className="meter-head">
                  <span>Disk</span>
                  <span className="muted small">{disk}</span>
                </div>
                <div className="meter">
                  <div className="meter-fill" style={{ width: `${diskUsedPct ?? 0}%` }} />
                </div>
              </div>
            )}
            {device.battery_percent != null && (
              <div>
                <div className="meter-head">
                  <span>Battery</span>
                  <span className="muted small">
                    {device.battery_percent}%
                    {device.power_plugged != null &&
                      (device.power_plugged ? " · charging" : " · on battery")}
                  </span>
                </div>
                <div className="meter">
                  <div
                    className="meter-fill meter-battery"
                    style={{ width: `${device.battery_percent}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="card">
        <h2 className="card-title">Application usage (last 7 days)</h2>
        {!usage || usage.apps.length === 0 ? (
          <p className="muted small">No usage reported yet.</p>
        ) : (
          <>
            <p className="muted small">
              Total active time: {formatDuration(usage.total_seconds)}
            </p>
            <ul className="usage-list">
              {usage.apps.slice(0, 12).map((a) => (
                <li key={a.app_name}>
                  <div className="usage-row-head">
                    <span className="usage-app">{a.app_name}</span>
                    <span className="muted small">{formatDuration(a.seconds)}</span>
                  </div>
                  <div className="meter">
                    <div
                      className="meter-fill meter-usage"
                      style={{ width: `${maxUsage ? (a.seconds / maxUsage) * 100 : 0}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <ScreenshotsPanel deviceUid={device.device_uid} />
      <RemoteSupportPanel deviceUid={device.device_uid} />

      <div className="future-grid">
        {FUTURE_SECTIONS.map((s) => (
          <section className="card card-muted" key={s.title}>
            <h2 className="card-title">{s.title}</h2>
            <p className="muted small">Not collected yet. Arrives in {s.milestone}.</p>
          </section>
        ))}
      </div>
    </div>
  );
}
