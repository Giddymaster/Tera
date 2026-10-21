import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";
import { ActivityPage } from "./pages/ActivityPage";
import { AndroidPage } from "./pages/AndroidPage";
import { ApplePage } from "./pages/ApplePage";
import { DashboardPage } from "./pages/DashboardPage";
import { DeviceDetailPage } from "./pages/DeviceDetailPage";
import { LoginPage } from "./pages/LoginPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/devices/:deviceUid" element={<DeviceDetailPage />} />
          <Route path="/activity" element={<ActivityPage />} />
          <Route path="/android" element={<AndroidPage />} />
          <Route path="/apple" element={<ApplePage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
