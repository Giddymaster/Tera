import { useEffect, useState } from "react";
import { getAppleStatus } from "../api/endpoints";
import type { AppleStatus } from "../api/types";

const CAP_LABEL: Record<string, string> = {
  inventory: "Device inventory",
  os_security_info: "OS / security info",
  managed_apps: "Managed app deployment",
  config_profiles: "Configuration profiles",
  remote_lock: "Remote lock",
  remote_wipe: "Remote wipe",
  lost_mode: "Managed Lost Mode",
  location: "Location",
  screenshots: "Screenshots",
  live_screen_view: "Live screen view",
  app_usage: "App usage / keystrokes",
};

function capCell(value: boolean | string) {
  if (value === true) return <span className="cap-yes">Available</span>;
  if (value === false) return <span className="cap-no">Not available</span>;
  if (value === "supervised_only")
    return <span className="cap-limited">Supervised only</span>;
  if (value === "lost_mode_supervised_only")
    return <span className="cap-limited">Lost Mode (supervised) only</span>;
  return <span className="cap-limited">{String(value)}</span>;
}

const SETUP_STEPS = [
  "Enroll your organization in Apple Business Manager (free; needs org verification).",
  "Obtain an APNs certificate for MDM. A self-hosted MDM needs an MDM vendor certificate (historically the Apple Developer Enterprise Program, ~$299/year).",
  "Stand up an MDM server (e.g. the open-source NanoMDM) behind this dashboard, trusting the current APNs certificate chain.",
  "Enroll company iPhones/iPads via Automated Device Enrollment (supervised) for full capability, then verify inventory, lock, and Lost Mode.",
];

export function ApplePage() {
  const [status, setStatus] = useState<AppleStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAppleStatus()
      .then(setStatus)
      .catch(() => setError("Could not load Apple MDM status."));
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Apple (iOS / iPadOS)</h1>
          <p className="muted small">Company-owned iPhones and iPads via Apple MDM</p>
        </div>
        {status && (
          <span className={`role-chip ${status.configured ? "role-owner" : ""}`}>
            {status.configured ? "Configured" : "Not configured"}
          </span>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        <h2 className="card-title">Status</h2>
        {!status ? (
          <p className="muted small">Loading…</p>
        ) : status.configured ? (
          <p className="small">
            MDM server configured at <span className="mono">{status.server_url}</span>.
            Enrolled Apple devices appear on the Dashboard alongside other devices.
          </p>
        ) : (
          <>
            <p className="small">
              Apple MDM is not configured. Unlike Android, there is no free,
              self-contained API: a working setup needs Apple Business Manager, an
              APNs certificate, and an MDM server. See{" "}
              <span className="mono">docs/apple-mdm-feasibility.md</span> for the full
              assessment and costs.
            </p>
            <h3 className="mini-title">Setup steps</h3>
            <ol className="setup-list">
              {SETUP_STEPS.map((s, i) => (
                <li key={i} className="small">
                  {s}
                </li>
              ))}
            </ol>
          </>
        )}
      </section>

      {status && (
        <section className="card">
          <h2 className="card-title">Enrollment models</h2>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Supervised</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {status.enrollment_models.map((m) => (
                  <tr key={m.name}>
                    <td>{m.name}</td>
                    <td>{m.supervised ? "Yes" : "No"}</td>
                    <td className="muted small">{m.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {status && (
        <section className="card">
          <h2 className="card-title">What Apple MDM can do</h2>
          <p className="muted small">
            Honest capability matrix. Screenshots, live screen view, and app usage
            are not possible via Apple MDM; location is available only through
            Managed Lost Mode on supervised devices.
          </p>
          <div className="table-wrap">
            <table className="table">
              <tbody>
                {Object.entries(status.capabilities).map(([key, value]) => (
                  <tr key={key}>
                    <td>{CAP_LABEL[key] ?? key}</td>
                    <td>{capCell(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
