import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Layout() {
  const { admin, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-name">Device Manager</span>
          </div>
          <nav className="nav">
            <NavLink to="/" end className="nav-link">
              Dashboard
            </NavLink>
            <NavLink to="/activity" className="nav-link">
              Activity
            </NavLink>
            <NavLink to="/android" className="nav-link">
              Android
            </NavLink>
            <NavLink to="/apple" className="nav-link">
              Apple
            </NavLink>
          </nav>
          <div className="topbar-right">
            {admin && (
              <span className="who">
                {admin.email}
                <span className={`role-chip role-${admin.role}`}>{admin.role}</span>
              </span>
            )}
            <button className="btn btn-ghost" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
