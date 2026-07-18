"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactElement } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient, ApiError } from "@/lib/api-client";
import { extractAuthErrorMessage, mapValidationIssues } from "@/lib/auth-errors";
import { hasStoredAccessCookie, setStoredAuth } from "@/lib/auth";
import { loginSchema, type LoginValues } from "@/lib/validators/auth.schema";

type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export default function LoginPage(): ReactElement {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  useEffect(() => {
    if (hasStoredAccessCookie()) {
      router.replace("/dashboard");
    }
  }, [router]);

  const onSubmit = async (values: LoginValues): Promise<void> => {
    setServerError(null);
    try {
      const response = await apiClient<LoginResponse>("/auth/login", {
        method: "POST",
        body: values,
      });
      setStoredAuth(response.access_token, response.expires_in);
      router.replace("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        const validationErrors = mapValidationIssues(error);
        Object.entries(validationErrors).forEach(([field, message]) => {
          setError(field as keyof LoginValues, { type: "server", message });
        });
      }
      setServerError(extractAuthErrorMessage(error));
    }
  };

  return (
    <AuthCard
      badge="Authentication"
      title="Welcome back"
      description="Sign in to Kara Orders and continue managing companies, products, and orders."
    >
      <CardHeader>
        <CardTitle>Login</CardTitle>
        <CardDescription>Use your company account to access the dashboard.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            {errors.email ? <p className="text-sm text-destructive">{errors.email.message}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
            {errors.password ? <p className="text-sm text-destructive">{errors.password.message}</p> : null}
          </div>
          {serverError ? <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{serverError}</p> : null}
          <Button className="w-full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Need an account?{" "}
            <Link className="font-medium text-foreground underline-offset-4 hover:underline" href="/register">
              Create one
            </Link>
          </p>
        </form>
      </CardContent>
    </AuthCard>
  );
}
