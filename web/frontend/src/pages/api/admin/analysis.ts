import type { NextApiRequest, NextApiResponse } from "next";
import { getAnalysisStore, type CreateAnalysisInput } from "../../../server/analysisStore";

function parseSnapshotId(value: string | string[] | undefined): number | undefined {
  if (value === undefined) {
    return undefined;
  }
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number.parseInt(raw, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
}

function normalizeCreatePayload(body: unknown): CreateAnalysisInput {
  if (!body || typeof body !== "object") {
    throw new Error("Payload must be an object");
  }
  const data = body as Record<string, unknown>;
  const snapshotId = Number.parseInt(String(data.snapshot_id ?? data.snapshotId ?? ""), 10);
  if (!Number.isFinite(snapshotId)) {
    throw new Error("snapshot_id is required");
  }
  const author = typeof data.author === "string" ? data.author : undefined;
  const title = typeof data.title === "string" ? data.title : undefined;
  if (!author || !title) {
    throw new Error("author and title are required");
  }
  const notes = typeof data.notes === "string" ? data.notes : undefined;
  const itemsInput = Array.isArray(data.items) ? data.items : [];
  const items = itemsInput
    .map((item) => (typeof item === "object" && item !== null ? item : null))
    .filter((item): item is Record<string, unknown> => item !== null)
    .map((item) => ({
      label: String(item.label ?? ""),
      score: Number.parseFloat(String(item.score ?? 0)) || 0,
      payload: item.payload,
    }))
    .filter((item) => item.label.length > 0);

  return {
    snapshotId,
    author,
    title,
    notes,
    items,
  };
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
): Promise<void> {
  const store = getAnalysisStore();

  if (req.method === "GET") {
    const snapshotId = parseSnapshotId(req.query.snapshot_id);
    const analyses = store.list(snapshotId);
    res.status(200).json(analyses);
    return;
  }

  if (req.method === "POST") {
    try {
      const payload = normalizeCreatePayload(req.body);
      const record = store.create(payload);
      res.status(201).json(record);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid payload";
      res.status(400).json({ error: message });
    }
    return;
  }

  res.setHeader("Allow", "GET, POST");
  res.status(405).end("Method Not Allowed");
}
