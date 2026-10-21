import { useCallback, useEffect, useState } from "react";
import {
  getDeviceLocation,
  requestLocation,
  updateLocationPolicy,
} from "../api/endpoints";
import type { DeviceLocation } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { formatDateTime, relativeTime } from "../lib/format";

const FRESH_LABEL: Record<string, string> = {
  current: "Current",
  stale: "Stale",
  none: "No location",
};

export function LocationCard({ deviceUid }: { deviceUid: string }) {
  const { hasPermission } = useAuth();
  const canRequest = hasPermission("manage_devices");
  const canManage = hasPermission("manage_security_policy");

  const [loc, setLoc] = useState<DeviceLocation | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoc(await getDeviceLocation(deviceUid));
    } catch {
      /* ignore */
    }
  }, [deviceUid]);

  useEffect(() => {
    void load();
  }, [load]);

  async function toggle(enabled: boolean) {
    try {
      await updateLocationPolicy(deviceUid, { enabled, retention_days: 30 });
      setNote(enabled ? "Location collection enabled." : "Location collection disabled.");
      await load();
    } catch {
      setNote("Could not change the policy (need the security-policy permission).");
    }
  }

  async function request() {
    try {
      await requestLocation(deviceUid);
      setNote("Location requested. It appears after the device responds.");
      setTimeout(() => void load(), 5000);
    } catch {
      setNote("Could not request a location.");
    }
  }

  const latest = loc?.latest ?? null;
  const freshness = loc?.freshness ?? "none";
  const mapUrl = latest
    ? `https://www.openstreetmap.org/?mlat=${latest.latitude}&mlon=${latest.longitude}#map=15/${latest.latitude}/${latest.longitude}`
    : null;

  return (
    <section className="card">
      <div className="card-title-row">
        <h2 className="card-title">Location</h2>
        <div className="card-actions">
          {loc && (
            <span className={`fresh fresh-${freshness}`}>{FRESH_LABEL[freshness]}</span>
          )}
          {canRequest && (
            <button className="btn btn-sm btn-primary" onClick={() => void request()}>
              Request location
            </button>
          )}
        </div>
      </div>

      <p className="muted small">
        Location is opt-in and not collected continuously. Each result shows its
        source and time. Laptops often have no location provider, and Android/iOS
        report location only via Lost Mode — in those cases this shows "unavailable"
        rather than a made-up coordinate.
      </p>

      {canManage && loc && (
        <label className="policy-row">
          <input
            type="checkbox"
            checked={loc.enabled}
            onChange={(e) => void toggle(e.target.checked)}
          />
          <span>Allow periodic location collection</span>
        </label>
      )}

      {latest ? (
        <dl className="detail-grid">
          <div>
            <dt>Coordinates</dt>
            <dd className="mono">
              {latest.latitude.toFixed(5)}, {latest.longitude.toFixed(5)}
            </dd>
          </div>
          <div>
            <dt>Accuracy</dt>
            <dd>{latest.accuracy_m != null ? `${latest.accuracy_m.toFixed(0)} m` : "—"}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{latest.source}</dd>
          </div>
          <div>
            <dt>Reported</dt>
            <dd>
              {formatDateTime(latest.captured_at)}
              <span className="muted small"> ({relativeTime(latest.captured_at)})</span>
            </dd>
          </div>
          {mapUrl && (
            <div>
              <dt>Map</dt>
              <dd>
                <a href={mapUrl} target="_blank" rel="noreferrer">
                  View on OpenStreetMap
                </a>
              </dd>
            </div>
          )}
        </dl>
      ) : (
        <p className="muted small">
          No location on record for this device. It may be disabled, unavailable on
          this hardware, or permission-restricted.
        </p>
      )}

      {note && <p className="muted small">{note}</p>}
    </section>
  );
}
