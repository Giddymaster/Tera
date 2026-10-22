import { useState } from "react";
import { getRustDesk } from "../api/endpoints";
import type { RustDeskInfo } from "../api/types";
import { useAuth } from "../auth/AuthContext";

// Full remote control via the self-hosted RustDesk server. The agent configures
// RustDesk and reports its ID + unattended password; an authorized admin reveals
// the connection details here and connects with the RustDesk client.
export function RemoteControlCard({
  deviceUid,
  rustdeskId,
}: {
  deviceUid: string;
  rustdeskId: string | null;
}) {
  const { hasPermission } = useAuth();
  const canUse = hasPermission("initiate_live_session");
  const [info, setInfo] = useState<RustDeskInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  async function reveal() {
    setError(null);
    try {
      setInfo(await getRustDesk(deviceUid));
    } catch {
      setError("Could not load the connection details.");
    }
  }

  function copy(label: string, text: string) {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), 1500);
    });
  }

  return (
    <section className="card">
      <h2 className="card-title">Remote control (RustDesk)</h2>
      <p className="muted small">
        Full, real-time remote control through your self-hosted RustDesk server.
        Connect using the RustDesk client (pointed at your server) with the ID and
        password below.
      </p>

      {!canUse ? (
        <p className="muted small">You need the live-session permission to use this.</p>
      ) : !rustdeskId ? (
        <p className="muted small">
          The agent hasn't set up RustDesk on this device yet. Once RustDesk is
          enabled on the server, the agent configures it on its next check-in and
          the ID appears here.
        </p>
      ) : !info ? (
        <>
          <div className="copy-row">
            <span className="copy-label">RustDesk ID</span>
            <code className="mono">{rustdeskId}</code>
          </div>
          <button className="btn btn-sm btn-primary" onClick={() => void reveal()}>
            Show connection details
          </button>
          {error && <p className="muted small">{error}</p>}
        </>
      ) : (
        <>
          <div className="copy-row">
            <span className="copy-label">RustDesk ID</span>
            <code className="mono">{info.rustdesk_id}</code>
            <button className="btn btn-sm" onClick={() => copy("id", info.rustdesk_id)}>
              {copied === "id" ? "Copied" : "Copy"}
            </button>
          </div>
          <div className="copy-row">
            <span className="copy-label">Password</span>
            <code className="mono">{info.password ?? "—"}</code>
            {info.password && (
              <button className="btn btn-sm" onClick={() => copy("pw", info.password!)}>
                {copied === "pw" ? "Copied" : "Copy"}
              </button>
            )}
          </div>
          <div className="copy-row">
            <span className="copy-label">Server</span>
            <code className="mono">{info.host || "—"}</code>
          </div>
          <p className="muted small">
            Open the RustDesk client configured for your server, enter the ID and
            password, and connect. Treat the password as a credential.
          </p>
        </>
      )}
    </section>
  );
}
