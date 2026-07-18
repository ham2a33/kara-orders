import { NextResponse, type NextRequest } from "next/server";

import { AUTH_COOKIE_NAMES } from "@/lib/auth";

const protectedPaths = [
  "/dashboard",
  "/products",
  "/orders",
  "/analytics",
  "/reports",
  "/settings",
  "/subscription",
  "/usage",
  "/billing",
  "/admin",
  "/audit",
  "/notifications",
  "/system-settings",
];

const authPaths = ["/login", "/register"];

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get(AUTH_COOKIE_NAMES.accessToken);

  if (authPaths.some((path) => pathname.startsWith(path)) && accessToken) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  const isProtectedPath = protectedPaths.some((path) => pathname.startsWith(path));

  if (!isProtectedPath) {
    return NextResponse.next();
  }

  if (accessToken) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/products/:path*",
    "/orders/:path*",
    "/analytics/:path*",
    "/reports/:path*",
    "/settings/:path*",
    "/subscription/:path*",
    "/usage/:path*",
    "/billing/:path*",
    "/admin/:path*",
    "/audit/:path*",
    "/notifications/:path*",
    "/system-settings/:path*",
  ],
};
