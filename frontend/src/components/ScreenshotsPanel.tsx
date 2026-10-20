import { useCallback, useEffect, useState } from "react";
import {
  deleteScreenshot,
  getScreenshotPolicy,
  listScreenshots,
  requestCapture,
  updateScreenshotPolicy,
} from "../api/endpoints";
import type { ScreenshotMeta, ScreenshotPolicy } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { relativeTime } from "../lib/format";
import { ScreenshotImage } from "./ScreenshotImage";

export function ScreenshotsPanel({ deviceUid }: { deviceUid: string }) {
  const { hasPermission } = useAuth();
  const canView = hasPermission("view_screenshots");
  const canManage = hasPermission("manage_security_policy");

  const [policy, setPolicy] = useState<ScreenshotPolicy | null>(null);
  const [shots, setShots] = useState<ScreenshotMeta[]>([]);
  const [note, setNote] = useState<string | null>(null);

  const loadShots = useCallback(async () => {
    if (!canView) return;
    try {
      setShots(await listScreenshots(deviceUid));
    } catch {
      /* ignore */
    }
  }, [deviceUid, canView]);

  useEffect(() => {
    getScreenshotPolicy(deviceUid).then(setPolicy).catch(() => undefined);
    void loadShots();
  }, [deviceUid, loadShots]);

  async function savePolicy() {
    if (!policy) return;
    try {
      setPolicy(await updateScreenshotPolicy(deviceUid, policy));
      setNote("Policy saved.");
    } catch {
      setNote("Could not save policy (need the security-policy permission).");
    }
  }

  async function capture() {
    try {
      await requestCapture(deviceUid);
      setNote("Capture requested. It appears after the device checks in.");
      setTimeout(() => void loadShots(), 4000);
    } catch {
      setNote("Could not request a capture.");
    }
  }

  async function remove(id: number) {
    await deleteScreenshot(id);
    setShots((s) => s.filter((x) => x.id !== id));
  }

  function set<K extends keyof ScreenshotPolicy>(key: K, value: ScreenshotPolicy[K]) {
    setPolicy((p) => (p ? { ...p, [key]: value } : p));
  }

  return (
    <section className="card">
      <div className="card-title-row">
        <h2 className="card-title">Screenshots</h2>
        {canView && (
          <div className="card-actions">
            <button className="btn btn-sm" onClick={() => void loadShots()}>
              Refresh
            </button>
            <button className="btn btn-sm btn-primary" onClick={() => void capture()}>
              Capture now
            </button>
          </div>
        )}
      </div>

      <p className="muted small">
        Captures run only under the policy below, with a monitoring notice shown on
        the device. Images are encrypted at rest and deleted after the retention
        period. Password fields cannot be reliably detected; use the excluded-apps
        list for sensitive apps.
      </p>

      {policy && (
        <div className="policy-grid">
          <label className="policy-row">
            <input
              type="checkbox"
              checked={policy.enabled}
              disabled={!canManage}
              onChange={(e) => set("enabled", e.target.checked)}
            />
            <span>Scheduled capture enabled</span>
          </label>
          <label className="policy-field">
            <span>Interval (minutes)</span>
            <input
              type="number"
              min={1}
              max={1440}
              value={policy.interval_minutes}
              disabled={!canManage}
              onChange={(e) => set("interval_minutes", Number(e.target.value))}
            />
          </label>
          <label className="policy-field">
            <span>Retention (days)</span>
            <input
              type="number"
              min={1}
              max={365}
              value={policy.retention_days}
              disabled={!canManage}
              onChange={(e) => set("retention_days", Number(e.target.value))}
            />
          </label>
          <label className="policy-field policy-wide">
            <span>Excluded apps (comma-separated)</span>
            <input
              type="text"
              placeholder="e.g. 1password.exe, keeper.exe"
              value={policy.excluded_apps ?? ""}
              disabled={!canManage}
              onChange={(e) => set("excluded_apps", e.target.value)}
            />
          </label>
          {canManage && (
            <div>
              <button className="btn btn-sm btn-primary" onClick={() => void savePolicy()}>
                Save policy
              </button>
            </div>
          )}
        </div>
      )}

      {note && <p className="muted small">{note}</p>}

      {!canView ? (
        <p className="muted small">
          You do not have permission to view captured screenshots.
        </p>
      ) : shots.length === 0 ? (
        <p className="muted small">No screenshots captured yet.</p>
      ) : (
        <div className="shot-grid">
          {shots.map((s) => (
            <figure className="shot" key={s.id}>
              <ScreenshotImage id={s.id} className="shot-img" />
              <figcaption>
                <span className="muted tiny">
                  {s.trigger} · {relativeTime(s.captured_at)}
                </span>
                <button className="link-danger tiny" onClick={() => void remove(s.id)}>
                  Delete
                </button>
              </figcaption>
            </figure>
          ))}
        </div>
      )}
    </section>
  );
}
