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
import { registerSchema, type RegisterValues } from "@/lib/validators/auth.schema";

type RegisterResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export default function RegisterPage(): ReactElement {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      companyName: "",
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  useEffect(() => {
    if (hasStoredAccessCookie()) {
      router.replace("/dashboard");
    }
  }, [router]);

  const onSubmit = async (values: RegisterValues): Promise<void> => {
    setServerError(null);
    try {
      const response = await apiClient<RegisterResponse>("/auth/register", {
        method: "POST",
        body: {
          company_name: values.companyName,
          full_name: values.fullName,
          email: values.email,
          password: values.password,
          confirm_password: values.confirmPassword,
        },
      });
      setStoredAuth(response.access_token, response.expires_in);
      router.replace("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        const validationErrors = mapValidationIssues(error);
        Object.entries(validationErrors).forEach(([field, message]) => {
          const mappedField =
            field === "company_name"
              ? "companyName"
              : field === "full_name"
                ? "fullName"
                : field === "confirm_password"
                  ? "confirmPassword"
                  : field;
          setError(mappedField as keyof RegisterValues, { type: "server", message });
        });
      }
      setServerError(extractAuthErrorMessage(error));
    }
  };

  return (
    <AuthCard
      badge="Company onboarding"
      title="Create your company account"
      description="Register once, then manage products, orders, invoices, AI, and analytics from one workspace."
    >
      <CardHeader>
        <CardTitle>Create account</CardTitle>
        <CardDescription>Set up a new company and your owner account.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-2">
            <Label htmlFor="companyName">Company name</Label>
            <Input id="companyName" autoComplete="organization" {...register("companyName")} />
            {errors.companyName ? <p className="text-sm text-destructive">{errors.companyName.message}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="fullName">Full name</Label>
            <Input id="fullName" autoComplete="name" {...register("fullName")} />
            {errors.fullName ? <p className="text-sm text-destructive">{errors.fullName.message}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            {errors.email ? <p className="text-sm text-destructive">{errors.email.message}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
            {errors.password ? <p className="text-sm text-destructive">{errors.password.message}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <Input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              {...register("confirmPassword")}
            />
            {errors.confirmPassword ? <p className="text-sm text-destructive">{errors.confirmPassword.message}</p> : null}
          </div>
          {serverError ? <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{serverError}</p> : null}
          <Button className="w-full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link className="font-medium text-foreground underline-offset-4 hover:underline" href="/login">
              Sign in
            </Link>
          </p>
        </form>
      </CardContent>
    </AuthCard>
  );
}
