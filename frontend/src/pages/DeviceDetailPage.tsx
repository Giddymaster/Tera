import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getDevice } from "../api/endpoints";
import type { DeviceOut } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { computeStatus } from "../lib/deviceStatus";
import { formatDateTime, relativeTime } from "../lib/format";

const OS_LABEL: Record<string, string> = {
  windows: "Windows",
  android: "Android",
  ios: "iOS",
};

// Sections that will be populated in later milestones. Shown here so the device
// page reflects the full plan honestly, without implying data exists yet.
const FUTURE_SECTIONS = [
  { title: "Application usage", milestone: "Milestone 5" },
  { title: "Screenshots & sessions", milestone: "Milestone 7" },
  { title: "Location", milestone: "Milestone 10" },
];

export function DeviceDetailPage() {
  const { deviceUid = "" } = useParams();
  const [device, setDevice] = useState<DeviceOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const d = await getDevice(deviceUid);
        if (active) setDevice(d);
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

      <div className="future-grid">
        {FUTURE_SECTIONS.map((s) => (
          <section className="card card-muted" key={s.title}>
            <h2 className="card-title">{s.title}</h2>
            <p className="muted small">
              Not collected yet. Arrives in {s.milestone}.
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
