export const AUTH_STORAGE_KEYS = {
  accessToken: "kara_orders_access_token",
  refreshToken: "kara_orders_refresh_token",
} as const;

export const AUTH_COOKIE_NAMES = {
  accessToken: "kara_orders_access_token",
  refreshToken: "kara_orders_refresh_token",
} as const;

export function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function setCookie(name: string, value: string, maxAgeSeconds: number): void {
  if (!isBrowser()) {
    return;
  }

  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax`;
}

function deleteCookie(name: string): void {
  if (!isBrowser()) {
    return;
  }

  document.cookie = `${encodeURIComponent(name)}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getStoredAccessToken(): string | null {
  if (!isBrowser()) {
    return null;
  }

  const fromStorage = window.localStorage.getItem(AUTH_STORAGE_KEYS.accessToken);
  if (fromStorage) {
    return fromStorage;
  }

  const cookiePrefix = `${encodeURIComponent(AUTH_COOKIE_NAMES.accessToken)}=`;
  const cookieEntry = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith(cookiePrefix));
  if (!cookieEntry) {
    return null;
  }

  return decodeURIComponent(cookieEntry.slice(cookiePrefix.length));
}

export function hasStoredAccessCookie(): boolean {
  if (!isBrowser()) {
    return false;
  }

  return document.cookie.includes(`${encodeURIComponent(AUTH_COOKIE_NAMES.accessToken)}=`);
}

export function setStoredAuth(
  accessToken: string,
  expiresInSeconds: number,
  refreshToken: string | null = null,
): void {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, accessToken);
  if (refreshToken) {
    window.localStorage.setItem(AUTH_STORAGE_KEYS.refreshToken, refreshToken);
  }
  setCookie(AUTH_COOKIE_NAMES.accessToken, accessToken, expiresInSeconds);
  if (refreshToken) {
    setCookie(AUTH_COOKIE_NAMES.refreshToken, refreshToken, 30 * 24 * 60 * 60);
  }
}

export function clearStoredAuth(): void {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEYS.accessToken);
  window.localStorage.removeItem(AUTH_STORAGE_KEYS.refreshToken);
  deleteCookie(AUTH_COOKIE_NAMES.accessToken);
  deleteCookie(AUTH_COOKIE_NAMES.refreshToken);
}
