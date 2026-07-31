import { getStoredAccessToken, isBrowser, setStoredAuth } from "@/lib/auth";
import { isNetworkFailure, networkFailureMessage } from "@/lib/network-error";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestInitWithJson = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export function resolveUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  if (!baseUrl) {
    return url;
  }

  const normalizedPath = url.replace(/^\/+/, "");
  return new URL(normalizedPath, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`).toString();
}

export function buildHeaders(init: RequestInitWithJson = {}): Headers {
  const headers = new Headers(init.headers);

  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (isBrowser()) {
    const accessToken = getStoredAccessToken();
    if (accessToken && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  return headers;
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshAccessTokenFromCookie(): Promise<boolean> {
  if (!isBrowser()) {
    return false;
  }
  if (refreshInFlight) {
    return refreshInFlight;
  }

  refreshInFlight = (async () => {
    let response: Response;
    try {
      response = await fetch(resolveUrl("/auth/refresh"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
        cache: "no-store",
      });
    } catch (error) {
      if (isNetworkFailure(error)) {
        return false;
      }
      throw error;
    }
    if (!response.ok) {
      return false;
    }
    const payload = (await response.json()) as { access_token: string; expires_in: number };
    setStoredAuth(payload.access_token, payload.expires_in);
    return true;
  })();

  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

async function ensureAccessToken(url: string): Promise<void> {
  if (!isBrowser() || getStoredAccessToken()) {
    return;
  }
  if (url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/refresh")) {
    return;
  }
  await refreshAccessTokenFromCookie();
}

async function performFetch(url: string, init: RequestInitWithJson, headers: Headers): Promise<Response> {
  try {
    return await fetch(resolveUrl(url), {
      ...init,
      headers,
      credentials: "include",
      body:
        init.body === undefined || init.body instanceof FormData
          ? init.body
          : JSON.stringify(init.body),
      cache: "no-store",
    });
  } catch (error) {
    if (isNetworkFailure(error)) {
      throw new ApiError(networkFailureMessage(), 0, { cause: String(error) });
    }
    throw error;
  }
}

export async function apiClient<T>(url: string, init: RequestInitWithJson = {}): Promise<T> {
  await ensureAccessToken(url);
  const headers = buildHeaders(init);

  const response = await performFetch(url, init, headers);

  if (response.status === 401 && !url.includes("/auth/")) {
    const refreshed = await refreshAccessTokenFromCookie();
    if (refreshed) {
      const retryHeaders = buildHeaders(init);
      const retryResponse = await performFetch(url, init, retryHeaders);
      if (retryResponse.ok) {
        return (await retryResponse.json()) as T;
      }
      const retryDetails = await retryResponse.json().catch(() => undefined);
      throw new ApiError(
        (retryDetails as { detail?: string } | undefined)?.detail ?? "Request failed",
        retryResponse.status,
        retryDetails,
      );
    }
  }

  if (!response.ok) {
    const details = await response.json().catch(() => undefined);
    throw new ApiError(
      (details as { detail?: string } | undefined)?.detail ?? "Request failed",
      response.status,
      details,
    );
  }

  return (await response.json()) as T;
}

export async function apiDownload(url: string, filename?: string, init: RequestInitWithJson = {}): Promise<void> {
  const headers = buildHeaders(init);
  const { body, ...requestInit } = init;
  void body;
  const response = await fetch(resolveUrl(url), {
    ...requestInit,
    headers,
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    const details = await response.json().catch(() => undefined);
    throw new ApiError(
      (details as { detail?: string } | undefined)?.detail ?? "Request failed",
      response.status,
      details,
    );
  }

  if (typeof window === "undefined") {
    return;
  }

  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename ?? "download";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(objectUrl);
}
