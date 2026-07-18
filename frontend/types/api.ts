export type ApiEnvelope<T> = {
  data: T;
  meta?: Record<string, unknown>;
};

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};
