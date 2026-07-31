import { ApiError } from "@/lib/api-client";
import { isNetworkFailure, networkFailureMessage } from "@/lib/network-error";

type ValidationIssue = {
  loc?: Array<string | number>;
  msg?: string;
};

function formatDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        const issue = item as ValidationIssue;
        if (issue.msg) {
          const field = issue.loc?.[issue.loc.length - 1];
          return typeof field === "string" ? `${field}: ${issue.msg}` : issue.msg;
        }
        return null;
      })
      .filter((value): value is string => Boolean(value));
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }
  return null;
}

export function extractErrorMessage(error: unknown): string {
  if (isNetworkFailure(error)) {
    return networkFailureMessage();
  }

  if (error instanceof ApiError) {
    if (error.status === 0) {
      return networkFailureMessage();
    }
    if (error.status >= 500) {
      const fromDetails = formatDetail(
        error.details && typeof error.details === "object" && "detail" in error.details
          ? (error.details as { detail: unknown }).detail
          : error.details,
      );
      return fromDetails ?? `Ошибка сервера (${error.status})`;
    }
    const fromDetails = formatDetail(error.details && typeof error.details === "object" && "detail" in error.details ? (error.details as { detail: unknown }).detail : error.details);
    if (fromDetails) {
      return fromDetails;
    }
    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error) {
    if (isNetworkFailure(error)) {
      return networkFailureMessage();
    }
    return error.message;
  }

  return "Не удалось выполнить запрос. Попробуйте снова.";
}

export function extractErrorDetails(error: unknown): string {
  if (error instanceof ApiError) {
    const parts = [`HTTP ${error.status}`, error.message];
    if (error.details !== undefined) {
      parts.push(JSON.stringify(error.details, null, 2));
    }
    return parts.join("\n\n");
  }
  if (error instanceof Error) {
    return error.stack ?? error.message;
  }
  return String(error);
}

export function mapValidationErrors(error: unknown): Record<string, string> {
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
