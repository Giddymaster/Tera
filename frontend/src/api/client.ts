// A small fetch wrapper that attaches the access token, transparently refreshes
// it once on a 401, and surfaces a typed error otherwise.
//
// Security note: tokens are kept in localStorage for simplicity in this
// milestone. localStorage is readable by any script on the page, so a future
// hardening step (planned for the security milestone) is to move to httpOnly,
// SameSite cookies issued by the backend. See docs for the tradeoff.

import type { TokenResponse } from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

const ACCESS_KEY = "edm.access";
const REFRESH_KEY = "edm.refresh";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

// Called when authentication is unrecoverable (refresh failed). The AuthContext
// registers a handler so it can clear state and redirect to the login page.
let onAuthError: (() => void) | null = null;
export function setAuthErrorHandler(fn: (() => void) | null): void {
  onAuthError = fn;
}

export const tokenStore = {
  get access(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: TokenResponse): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

async function parseError(res: Response): Promise<ApiError> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") detail = body.detail;
    else if (Array.isArray(body?.detail)) detail = "Invalid input";
  } catch {
    /* non-JSON body */
  }
  return new ApiError(res.status, detail);
}

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  tokenStore.set((await res.json()) as TokenResponse);
  return true;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean; // attach access token (default true)
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
  _retry = true,
): Promise<T> {
  const { method = "GET", body, auth = true } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && tokenStore.access) {
    headers["Authorization"] = `Bearer ${tokenStore.access}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && _retry) {
    if (await tryRefresh()) {
      return apiRequest<T>(path, options, false);
    }
    tokenStore.clear();
    onAuthError?.();
    throw await parseError(res);
  }

  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Fetch a binary response (e.g. a screenshot image) with the same auth and
// one-time refresh behavior as apiRequest.
export async function apiBlob(path: string, _retry = true): Promise<Blob> {
  const headers: Record<string, string> = {};
  if (tokenStore.access) headers["Authorization"] = `Bearer ${tokenStore.access}`;
  const res = await fetch(`${BASE_URL}${path}`, { headers });
  if (res.status === 401 && _retry) {
    if (await tryRefresh()) return apiBlob(path, false);
    tokenStore.clear();
    onAuthError?.();
    throw new ApiError(401, "Not authenticated");
  }
  if (!res.ok) throw await parseError(res);
  return res.blob();
}

export { BASE_URL };
