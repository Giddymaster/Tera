import { useCallback, useEffect, useState } from "react";
import { listAuditLogs } from "../api/endpoints";
import type { AuditLogOut } from "../api/types";
import { formatDateTime, relativeTime } from "../lib/format";

// Friendly labels for known audit actions.
const ACTION_LABEL: Record<string, string> = {
  "admin.login": "Admin signed in",
  "admin.login_failed": "Failed sign-in",
  "device.create": "Device registered",
  "device.revoke": "Device revoked",
  "device.delete": "Device deleted",
  "device.enroll": "Device enrolled",
  "device.enroll_failed": "Failed enrollment",
};

export function ActivityPage() {
  const [rows, setRows] = useState<AuditLogOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setRows(await listAuditLogs(100));
    } catch {
      setError("Could not load the activity log.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Activity</h1>
          <p className="muted small">Audit log of administrator and device actions</p>
        </div>
        <button className="btn btn-ghost" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="centered muted">Loading activity…</div>
      ) : rows.length === 0 ? (
        <div className="empty">No activity recorded yet.</div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>When</th>
                <th>Action</th>
                <th>Actor</th>
                <th>Target</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td title={formatDateTime(r.timestamp)} className="muted">
                    {relativeTime(r.timestamp)}
                  </td>
                  <td>{ACTION_LABEL[r.action] ?? r.action}</td>
                  <td>{r.actor_email ?? "—"}</td>
                  <td className="mono tiny">{r.target_id ?? "—"}</td>
                  <td className="muted tiny">{r.ip_address ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
