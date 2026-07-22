import { apiClient } from "@/lib/api-client";
import type {
  AIRecognition,
  AIRecognitionConfirmPayload,
  AIRecognitionConfirmResponse,
  AIRecognitionItemSelectionPayload,
  AIRecognitionListResponse,
} from "@/types/ai";

type RecognitionQuery = {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  inputType?: string;
};

function buildQuery(params: RecognitionQuery = {}): string {
  const searchParams = new URLSearchParams();
  if (params.page) {
    searchParams.set("page", String(params.page));
  }
  if (params.pageSize) {
    searchParams.set("page_size", String(params.pageSize));
  }
  if (params.search) {
    searchParams.set("search", params.search);
  }
  if (params.status) {
    searchParams.set("status", params.status);
  }
  if (params.inputType) {
    searchParams.set("input_type", params.inputType);
  }
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getAIRecognitions(params: RecognitionQuery = {}): Promise<AIRecognitionListResponse> {
  return apiClient<AIRecognitionListResponse>(`/ai/order-recognitions${buildQuery(params)}`);
}

export async function getAIRecognition(recognitionId: string): Promise<AIRecognition> {
  return apiClient<AIRecognition>(`/ai/order-recognitions/${recognitionId}`);
}

export async function recognizeText(text: string): Promise<AIRecognition> {
  return apiClient<AIRecognition>("/ai/order-recognitions/text", {
    method: "POST",
    body: { text },
  });
}

export async function recognizePhoto(file: File): Promise<AIRecognition> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<AIRecognition>("/ai/order-recognitions/photo", {
    method: "POST",
    body: formData,
  });
}

export async function recognizeVoice(file: File): Promise<AIRecognition> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<AIRecognition>("/ai/order-recognitions/voice", {
    method: "POST",
    body: formData,
  });
}

export async function recognizePdf(file: File): Promise<AIRecognition> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<AIRecognition>("/ai/order-recognitions/pdf", {
    method: "POST",
    body: formData,
  });
}

export async function confirmRecognition(
  recognitionId: string,
  payload: AIRecognitionConfirmPayload,
): Promise<AIRecognitionConfirmResponse> {
  return apiClient<AIRecognitionConfirmResponse>(`/ai/order-recognitions/${recognitionId}/confirm`, {
    method: "POST",
    body: payload,
  });
}

export async function updateRecognitionItemSelection(
  recognitionId: string,
  itemIndex: number,
  payload: AIRecognitionItemSelectionPayload,
): Promise<AIRecognition> {
  return apiClient<AIRecognition>(`/ai/order-recognitions/${recognitionId}/items/${itemIndex}/selection`, {
    method: "PATCH",
    body: payload,
  });
}
