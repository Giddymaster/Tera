import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listDevices } from "../api/endpoints";
import type { DeviceOut } from "../api/types";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { computeStatus, type LiveStatus } from "../lib/deviceStatus";
import { relativeTime } from "../lib/format";

const OS_LABEL: Record<string, string> = {
  windows: "Windows",
  android: "Android",
  ios: "iOS",
};

export function DashboardPage() {
  const [devices, setDevices] = useState<DeviceOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await listDevices();
      setDevices(data);
      setRefreshedAt(new Date());
    } catch {
      setError("Could not load devices. Is the backend running and are you signed in?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const counts = useMemo(() => {
    const c = { total: devices.length, online: 0, offline: 0, pending: 0, revoked: 0 };
    for (const d of devices) {
      const s: LiveStatus = computeStatus(d);
      c[s] += 1;
    }
    return c;
  }, [devices]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return devices;
    return devices.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        (d.assigned_to ?? "").toLowerCase().includes(q) ||
        d.os_type.includes(q),
    );
  }, [devices, query]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Devices</h1>
          <p className="muted small">
            {refreshedAt
              ? `Last updated ${relativeTime(refreshedAt.toISOString())}`
              : "Loading…"}
          </p>
        </div>
        <button className="btn btn-ghost" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      <div className="stat-grid">
        <StatCard label="Total devices" value={counts.total} />
        <StatCard label="Online" value={counts.online} tone="online" />
        <StatCard label="Offline" value={counts.offline} tone="offline" />
        <StatCard label="Awaiting check-in" value={counts.pending} tone="pending" />
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="toolbar">
        <input
          className="search"
          type="search"
          placeholder="Search by name, assignee, or OS…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="centered muted">Loading devices…</div>
      ) : filtered.length === 0 ? (
        <div className="empty">
          {devices.length === 0
            ? "No devices registered yet. Seed demo devices from the backend to see them here."
            : "No devices match your search."}
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Device</th>
                <th>OS</th>
                <th>Assigned to</th>
                <th>Status</th>
                <th>Last check-in</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d) => (
                <tr key={d.device_uid}>
                  <td>
                    <Link to={`/devices/${d.device_uid}`} className="link-strong">
                      {d.name}
                    </Link>
                    <div className="muted tiny">{d.device_type}</div>
                  </td>
                  <td>{OS_LABEL[d.os_type] ?? d.os_type}</td>
                  <td>{d.assigned_to ?? "—"}</td>
                  <td>
                    <StatusBadge status={computeStatus(d)} />
                  </td>
                  <td className="muted">{relativeTime(d.last_seen_at)}</td>
                  <td className="row-action">
                    <Link to={`/devices/${d.device_uid}`} className="btn btn-sm">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
