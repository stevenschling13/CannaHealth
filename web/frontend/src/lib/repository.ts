import { listAnalysis, saveAnalysis, StoredAnalysis } from "./db";

export interface CreateAnalysisPayload {
  snapshotId: number;
  author: string;
  title: string;
  notes?: string;
  items: StoredAnalysis["items"];
}

export async function createAnalysis(payload: CreateAnalysisPayload): Promise<StoredAnalysis> {
  const record: StoredAnalysis = {
    ...payload,
    createdAt: new Date().toISOString(),
  };
  const id = await saveAnalysis(record);
  return { ...record, id };
}

export async function fetchAnalysis(): Promise<StoredAnalysis[]> {
  return listAnalysis();
}
