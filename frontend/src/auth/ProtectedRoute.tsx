import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute() {
  const { admin, loading } = useAuth();
  if (loading) {
    return <div className="centered muted">Loading…</div>;
  }
  if (!admin) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
