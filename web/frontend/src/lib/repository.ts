import { apiRequest, StoredAnalysis } from "./db";

export interface CreateAnalysisPayload {
  snapshotId: number;
  author: string;
  title: string;
  notes?: string | null;
  items: StoredAnalysis["items"];
}

interface ApiAnalysisItem {
  id?: number;
  analysis_id?: number;
  label: string;
  score: number;
  payload?: unknown;
}

interface ApiAnalysis {
  id: number;
  snapshot_id: number;
  created_at?: string;
  author: string;
  title: string;
  notes?: string | null;
  items?: ApiAnalysisItem[];
}

function normalizeAnalysis(data: ApiAnalysis): StoredAnalysis {
  return {
    id: data.id,
    snapshotId: data.snapshot_id,
    author: data.author,
    title: data.title,
    notes: data.notes ?? undefined,
    createdAt: data.created_at,
    items:
      data.items?.map((item) => ({
        id: item.id,
        analysisId: item.analysis_id,
        label: item.label,
        score: item.score,
        payload: item.payload,
      })) ?? [],
  };
}

export async function createAnalysis(payload: CreateAnalysisPayload): Promise<StoredAnalysis> {
  const body = {
    snapshot_id: payload.snapshotId,
    author: payload.author,
    title: payload.title,
    notes: payload.notes,
    items: payload.items.map((item) => ({
      label: item.label,
      score: item.score,
      payload: item.payload,
    })),
  };
  const response = await apiRequest<ApiAnalysis>("/admin/analysis", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return normalizeAnalysis(response);
}

export async function fetchAnalysis(snapshotId?: number): Promise<StoredAnalysis[]> {
  const response = await apiRequest<ApiAnalysis[]>("/admin/analysis", {}, {
    snapshot_id: snapshotId,
  });
  return response.map(normalizeAnalysis);
}
