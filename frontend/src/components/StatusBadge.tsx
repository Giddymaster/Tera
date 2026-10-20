import { STATUS_LABEL, type LiveStatus } from "../lib/deviceStatus";

export function StatusBadge({ status }: { status: LiveStatus }) {
  return (
    <span className={`status status-${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {STATUS_LABEL[status]}
    </span>
  );
}
