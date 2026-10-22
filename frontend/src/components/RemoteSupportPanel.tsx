import { useCallback, useEffect, useState } from "react";
import {
  endSession,
  getSessionScreenshots,
  listSessions,
  startSession,
} from "../api/endpoints";
import type { RemoteSession, ScreenshotMeta } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { formatDateTime, relativeTime } from "../lib/format";
import { ScreenshotImage } from "./ScreenshotImage";

export function RemoteSupportPanel({ deviceUid }: { deviceUid: string }) {
  const { hasPermission } = useAuth();
  const canInitiate = hasPermission("initiate_live_session");
  const canViewFrames = hasPermission("view_screenshots");

  const [sessions, setSessions] = useState<RemoteSession[]>([]);
  const [frames, setFrames] = useState<ScreenshotMeta[]>([]);
  const [note, setNote] = useState<string | null>(null);

  const active = sessions.find((s) => s.status === "active") ?? null;

  const loadSessions = useCallback(async () => {
    try {
      setSessions(await listSessions(deviceUid));
    } catch {
      /* ignore */
    }
  }, [deviceUid]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  // While a session is active, poll for the latest snapshots.
  useEffect(() => {
    if (!active || !canViewFrames) {
      setFrames([]);
      return;
    }
    let active_ = true;
    const tick = () =>
      getSessionScreenshots(active.id)
        .then((f) => {
          if (active_) setFrames(f);
        })
        .catch(() => undefined);
    void tick();
    const timer = setInterval(tick, 1500);
    return () => {
      active_ = false;
      clearInterval(timer);
    };
  }, [active, canViewFrames]);

  async function start() {
    try {
      await startSession(deviceUid);
      setNote("Session started. A consent notice is shown on the device.");
      await loadSessions();
    } catch {
      setNote("Could not start a session (need the live-session permission).");
    }
  }

  async function stop(id: number) {
    await endSession(id);
    setNote("Session ended.");
    await loadSessions();
  }

  return (
    <section className="card">
      <div className="card-title-row">
        <h2 className="card-title">Live remote support</h2>
        {canInitiate && !active && (
          <button className="btn btn-sm btn-primary" onClick={() => void start()}>
            Start session
          </button>
        )}
      </div>

      <p className="muted small">
        A session shows a visible notice on the device and streams near-live
        snapshots over an authenticated, encrypted connection. Sessions are not
        recorded beyond the retained snapshots. For full-motion remote control,
        integrate an established tool (e.g. WebRTC or RustDesk) in production.
      </p>

      {active ? (
        <div className="session-live">
          <div className="session-banner">
            <span className="status status-online">
              <span className="status-dot" aria-hidden="true" /> Live
            </span>
            <span className="muted small">
              Started {relativeTime(active.started_at)} by{" "}
              {active.initiated_by_email ?? "an administrator"}
            </span>
            {canInitiate && (
              <button className="btn btn-sm" onClick={() => void stop(active.id)}>
                End session
              </button>
            )}
          </div>
          {canViewFrames ? (
            frames.length > 0 ? (
              <ScreenshotImage id={frames[0].id} className="session-frame" />
            ) : (
              <div className="shot-ph shot-loading session-frame" />
            )
          ) : (
            <p className="muted small">
              You cannot view the live frames (need the screenshots permission).
            </p>
          )}
        </div>
      ) : (
        <p className="muted small">
          {canInitiate ? "No active session." : "No active session."}
        </p>
      )}

      {note && <p className="muted small">{note}</p>}

      {sessions.length > 0 && (
        <div className="session-history">
          <h3 className="mini-title">Recent sessions</h3>
          <ul className="session-list">
            {sessions.slice(0, 6).map((s) => (
              <li key={s.id}>
                <span className={`dot dot-${s.status}`} aria-hidden="true" />
                <span className="muted small">
                  {formatDateTime(s.started_at)} ·{" "}
                  {s.initiated_by_email ?? "admin"} ·{" "}
                  {s.status === "active" ? "active" : `ended ${relativeTime(s.ended_at)}`}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
