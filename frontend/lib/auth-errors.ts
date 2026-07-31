import { ApiError } from "@/lib/api-client";
import { extractErrorMessage } from "@/lib/errors";

type ValidationIssue = {
  loc?: Array<string | number>;
  msg?: string;
};

export function extractAuthErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    const detail = extractErrorMessage(error);
    if (detail && detail !== "Request failed") {
      return detail;
    }
    return "Неверный email или пароль";
  }

  return extractErrorMessage(error);
}

export function mapValidationIssues(error: unknown): Record<string, string> {
  if (!error || typeof error !== "object" || !("details" in error)) {
    return {};
  }

  const details = (error as ApiError).details;
  if (!Array.isArray(details)) {
    return {};
  }

  return details.reduce<Record<string, string>>((accumulator, item) => {
    const issue = item as ValidationIssue;
    const field = issue.loc?.[issue.loc.length - 1];
    if (typeof field === "string" && issue.msg) {
      accumulator[field] = issue.msg;
    }
    return accumulator;
  }, {});
}
