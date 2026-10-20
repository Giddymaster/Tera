import { useEffect, useState } from "react";
import { getAndroidStatus } from "../api/endpoints";
import type { AndroidStatus } from "../api/types";

const CAP_LABEL: Record<string, string> = {
  inventory: "Device inventory",
  compliance: "Compliance / security status",
  managed_apps: "Managed app install",
  remote_lock: "Remote lock",
  remote_wipe: "Remote wipe",
  reboot: "Reboot",
  location: "Location",
  screenshots: "Screenshots",
  live_screen_view: "Live screen view",
  app_usage: "App usage / keystrokes",
};

function capCell(value: boolean | string) {
  if (value === true) return <span className="cap-yes">Available</span>;
  if (value === false) return <span className="cap-no">Not available</span>;
  if (value === "lost_mode_only")
    return <span className="cap-limited">Lost Mode only</span>;
  return <span className="cap-limited">{String(value)}</span>;
}

const SETUP_STEPS = [
  "Create a Google Cloud project and enable the Android Management API (free).",
  "Create a service account, download its JSON key, and set ANDROID_SA_JSON and ANDROID_PROJECT_ID.",
  "Run the enterprise signup flow and set ANDROID_ENTERPRISE_NAME (e.g. enterprises/LC...).",
  "Restart the backend, then generate a QR enrollment token and scan it on a factory-reset test phone.",
];

export function AndroidPage() {
  const [status, setStatus] = useState<AndroidStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAndroidStatus()
      .then(setStatus)
      .catch(() => setError("Could not load Android status."));
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Android management</h1>
          <p className="muted small">
            Company-owned Android devices via the Android Management API
          </p>
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
            Connected to enterprise <span className="mono">{status.enterprise_name}</span>{" "}
            (project <span className="mono">{status.project_id}</span>). Enrolled
            devices appear on the Dashboard alongside Windows devices.
          </p>
        ) : (
          <>
            <p className="small">
              The Android Management API integration is not configured yet, so no
              Android devices can be enrolled or managed. The capabilities below are
              what this platform supports once configured. Setup is free (no
              per-device Google fee); see{" "}
              <span className="mono">docs/android-feasibility.md</span>.
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
          <h2 className="card-title">What Android management can do</h2>
          <p className="muted small">
            Honest capability matrix. Screenshots, live screen view, and app usage
            are not available through Android MDM — those are Windows-agent features.
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
