export function isNetworkFailure(error: unknown): boolean {
  if (error instanceof TypeError) {
    return true;
  }
  if (error instanceof Error) {
    return /load failed|failed to fetch|networkerror|network request failed/i.test(error.message);
  }
  return false;
}

export function networkFailureMessage(): string {
  return "Не удалось подключиться к API. Проверьте, что backend запущен и доступен.";
}
