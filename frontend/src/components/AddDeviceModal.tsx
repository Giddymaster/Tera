import { useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { createDevice } from "../api/endpoints";
import type { DeviceCreateResponse, DeviceType, OSType } from "../api/types";

// Modal to register a new device. On success it shows the device id and the
// one-time enrollment secret (which is never retrievable again), ready to paste
// into the agent's config.json.
export function AddDeviceModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [osType, setOsType] = useState<OSType>("windows");
  const [deviceType, setDeviceType] = useState<DeviceType>("laptop");
  const [assignee, setAssignee] = useState("");
  const [result, setResult] = useState<DeviceCreateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const apiBase = `${window.location.origin}/api`;
  const installCmd = result
    ? `$env:TERA_UID="${result.device.device_uid}"; $env:TERA_SECRET="${result.enrollment_secret}"; $env:TERA_URL="${apiBase}"; irm https://raw.githubusercontent.com/Giddymaster/Tera/main/windows-agent/bootstrap.ps1 | iex`
    : "";

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const r = await createDevice({
        name: name.trim(),
        os_type: osType,
        device_type: deviceType,
        assigned_to: assignee.trim() || null,
      });
      setResult(r);
      onCreated();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 403
          ? "You need the manage-devices permission to add a device."
          : "Could not create the device.",
      );
    } finally {
      setBusy(false);
    }
  }

  function copy(label: string, text: string) {
    navigator.clipboard?.writeText(text).then(
      () => {
        setCopied(label);
        setTimeout(() => setCopied(null), 1500);
      },
      () => undefined,
    );
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {!result ? (
          <form onSubmit={submit}>
            <h2 className="card-title">Register a device</h2>
            {error && <div className="alert alert-error">{error}</div>}
            <label className="field">
              <span>Device name</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Reception Laptop"
                required
                autoFocus
              />
            </label>
            <div className="modal-row">
              <label className="field">
                <span>Operating system</span>
                <select value={osType} onChange={(e) => setOsType(e.target.value as OSType)}>
                  <option value="windows">Windows</option>
                  <option value="android">Android</option>
                  <option value="ios">iOS</option>
                </select>
              </label>
              <label className="field">
                <span>Device type</span>
                <select
                  value={deviceType}
                  onChange={(e) => setDeviceType(e.target.value as DeviceType)}
                >
                  <option value="laptop">Laptop</option>
                  <option value="phone">Phone</option>
                  <option value="tablet">Tablet</option>
                </select>
              </label>
            </div>
            <label className="field">
              <span>Assigned to (optional)</span>
              <input
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                placeholder="e.g. A. Rivera"
              />
            </label>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                {busy ? "Creating…" : "Create device"}
              </button>
            </div>
          </form>
        ) : (
          <div>
            <h2 className="card-title">Device created</h2>
            <div className="alert alert-warn">
              Copy the enrollment secret now — it is shown only once and cannot be
              retrieved again.
            </div>
            <div className="copy-row">
              <span className="copy-label">Device id</span>
              <code className="mono">{result.device.device_uid}</code>
              <button className="btn btn-sm" onClick={() => copy("uid", result.device.device_uid)}>
                {copied === "uid" ? "Copied" : "Copy"}
              </button>
            </div>
            <div className="copy-row">
              <span className="copy-label">Enrollment secret</span>
              <code className="mono">{result.enrollment_secret}</code>
              <button
                className="btn btn-sm"
                onClick={() => copy("secret", result.enrollment_secret)}
              >
                {copied === "secret" ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="muted small">
              <strong>One-command install (Windows):</strong> run this in PowerShell
              on the laptop. It installs and auto-starts the agent. (Python required:
              <span className="mono"> winget install -e --id Python.Python.3.12</span>)
            </p>
            <pre className="config-snippet">{installCmd}</pre>
            <button className="btn btn-sm" onClick={() => copy("cmd", installCmd)}>
              {copied === "cmd" ? "Copied" : "Copy command"}
            </button>

            <details className="manual-details">
              <summary className="muted small">Or configure manually (config.json)</summary>
              <pre className="config-snippet">{`{
  "server_url": "${apiBase}",
  "device_uid": "${result.device.device_uid}",
  "enrollment_secret": "${result.enrollment_secret}"
}`}</pre>
            </details>

            <div className="modal-actions">
              <button className="btn btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
