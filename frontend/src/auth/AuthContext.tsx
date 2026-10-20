import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { setAuthErrorHandler, tokenStore } from "../api/client";
import { getMe, login as apiLogin } from "../api/endpoints";
import type { AdminOut } from "../api/types";

interface AuthContextValue {
  admin: AdminOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminOut | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a session on first load if we still hold tokens.
  useEffect(() => {
    let active = true;
    async function restore() {
      if (!tokenStore.access) {
        setLoading(false);
        return;
      }
      try {
        const me = await getMe();
        if (active) setAdmin(me);
      } catch {
        tokenStore.clear();
      } finally {
        if (active) setLoading(false);
      }
    }
    void restore();
    return () => {
      active = false;
    };
  }, []);

  // When a refresh ultimately fails, drop the session.
  useEffect(() => {
    setAuthErrorHandler(() => setAdmin(null));
    return () => setAuthErrorHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiLogin(email, password);
    setAdmin(me);
  }, []);

  const logout = useCallback(() => {
    tokenStore.clear();
    setAdmin(null);
  }, []);

  const hasPermission = useCallback(
    (permission: string) => admin?.permissions.includes(permission) ?? false,
    [admin],
  );

  return (
    <AuthContext.Provider value={{ admin, loading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
