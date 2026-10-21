import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAlerts, getReportSummary } from "../api/endpoints";
import type { Alert, ReportSummary } from "../api/types";
import { StatCard } from "../components/StatCard";

const OS_LABEL: Record<string, string> = {
  windows: "Windows",
  android: "Android",
  ios: "iOS",
};

export function ReportsPage() {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [s, a] = await Promise.all([getReportSummary(), getAlerts()]);
      setSummary(s);
      setAlerts(a);
    } catch {
      setError("Could not load the report.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Reports</h1>
          <p className="muted small">Fleet summary and active alerts</p>
        </div>
        <button className="btn btn-ghost" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {summary && (
        <>
          <div className="stat-grid">
            <StatCard label="Total devices" value={summary.total_devices} />
            <StatCard label="Online" value={summary.online} tone="online" />
            <StatCard label="Offline" value={summary.offline} tone="offline" />
            <StatCard
              label="Alerts (warnings)"
              value={summary.alerts_warning}
              tone="pending"
            />
          </div>

          <section className="card">
            <h2 className="card-title">Fleet</h2>
            <dl className="detail-grid">
              <div>
                <dt>By OS</dt>
                <dd>
                  {Object.entries(summary.by_os)
                    .map(([os, n]) => `${OS_LABEL[os] ?? os}: ${n}`)
                    .join(" · ") || "—"}
                </dd>
              </div>
              <div>
                <dt>Awaiting enrollment</dt>
                <dd>{summary.pending}</dd>
              </div>
              <div>
                <dt>Active support sessions</dt>
                <dd>{summary.active_sessions}</dd>
              </div>
              <div>
                <dt>Agent updates available</dt>
                <dd>{summary.updates_available}</dd>
              </div>
              <div>
                <dt>Screenshots stored</dt>
                <dd>{summary.screenshots_total}</dd>
              </div>
              <div>
                <dt>Revoked devices</dt>
                <dd>{summary.revoked}</dd>
              </div>
            </dl>
          </section>
        </>
      )}

      <section className="card">
        <h2 className="card-title">Active alerts</h2>
        {alerts.length === 0 ? (
          <p className="muted small">No active alerts.</p>
        ) : (
          <ul className="alert-list">
            {alerts.map((a, i) => (
              <li key={`${a.device_uid}-${a.type}-${i}`}>
                <span className={`alert-dot alert-${a.severity}`} aria-hidden="true" />
                <Link to={`/devices/${a.device_uid}`} className="link-strong">
                  {a.device_name}
                </Link>
                <span className="muted small">{a.message}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
