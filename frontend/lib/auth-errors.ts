import type { ApiError } from "@/lib/api-client";

type ValidationIssue = {
  loc?: Array<string | number>;
  msg?: string;
};

export function extractAuthErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed";
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
