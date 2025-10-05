export interface StoredAnalysisItem {
  id?: number;
  analysisId?: number;
  label: string;
  score: number;
  payload?: unknown;
}

export interface StoredAnalysis {
  id?: number;
  snapshotId: number;
  author: string;
  title: string;
  notes?: string | null;
  createdAt?: string;
  items: StoredAnalysisItem[];
}

const DEFAULT_BASE_URL = "http://localhost:8000";

function resolveBaseUrl(): string {
  const envUrl =
    (typeof process !== "undefined" &&
      (process.env.NEXT_PUBLIC_API_BASE_URL || process.env.REACT_APP_API_BASE_URL)) ||
    "";
  if (envUrl) {
    return envUrl;
  }
  if (typeof window !== "undefined" && window.location.origin) {
    return window.location.origin;
  }
  return DEFAULT_BASE_URL;
}

export function buildApiUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const baseUrl = resolveBaseUrl();
  const url = new URL(path, baseUrl);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

type RequestOptions = RequestInit & { expectJson?: boolean };

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
  params?: Record<string, string | number | undefined>
): Promise<T> {
  const url = buildApiUrl(path, params);
  const { expectJson = true, ...init } = options;
  const headers = new Headers(init.headers as HeadersInit | undefined);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (!expectJson) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}
