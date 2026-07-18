import { AUTH_STORAGE_KEYS, isBrowser } from "@/lib/auth";

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

  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (!baseUrl) {
    return url;
  }

  const normalizedPath = url.replace(/^\/+/, "");
  return new URL(normalizedPath, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`).toString();
}

function buildHeaders(init: RequestInitWithJson = {}): Headers {
  const headers = new Headers(init.headers);

  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (isBrowser()) {
    const accessToken = window.localStorage.getItem(AUTH_STORAGE_KEYS.accessToken);
    if (accessToken && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  return headers;
}

export async function apiClient<T>(url: string, init: RequestInitWithJson = {}): Promise<T> {
  const headers = buildHeaders(init);

  const response = await fetch(resolveUrl(url), {
    ...init,
    headers,
    credentials: "include",
    body:
      init.body === undefined || init.body instanceof FormData
        ? init.body
        : JSON.stringify(init.body),
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
