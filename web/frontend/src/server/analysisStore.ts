import { randomUUID } from "crypto";
import type { StoredAnalysis, StoredAnalysisItem } from "../lib/db";

export interface CreateAnalysisInput {
  snapshotId: number;
  author: string;
  title: string;
  notes?: string | null;
  items?: Array<Omit<StoredAnalysisItem, "id" | "analysisId">>;
}

interface AnalysisState {
  nextAnalysisId: number;
  nextItemId: number;
  analyses: Map<number, StoredAnalysis>;
}

function cloneAnalysis(analysis: StoredAnalysis): StoredAnalysis {
  return {
    ...analysis,
    items: analysis.items.map((item) => ({ ...item })),
  };
}

function createInitialState(): AnalysisState {
  const createdAt = new Date().toISOString();
  const initialAnalysis: StoredAnalysis = {
    id: 1,
    snapshotId: 101,
    author: "System",
    title: "Initial deployment validation",
    notes: "Seeded analysis to verify deployment wiring.",
    createdAt,
    items: [
      {
        id: 1,
        analysisId: 1,
        label: "deployment-status",
        score: 1,
        payload: { message: "Vercel preview seeded" },
      },
    ],
  };

  return {
    nextAnalysisId: 2,
    nextItemId: 2,
    analyses: new Map([[initialAnalysis.id!, initialAnalysis]]),
  };
}

function getGlobalStore(): AnalysisStore {
  const globalWithStore = globalThis as typeof globalThis & {
    __cannaHealthAnalysisStore?: AnalysisStore;
  };

  if (!globalWithStore.__cannaHealthAnalysisStore) {
    globalWithStore.__cannaHealthAnalysisStore = new AnalysisStore();
  }

  return globalWithStore.__cannaHealthAnalysisStore;
}

export class AnalysisStore {
  private state: AnalysisState;

  constructor(initialState: AnalysisState | null = null) {
    this.state = initialState ?? createInitialState();
  }

  public list(snapshotId?: number): StoredAnalysis[] {
    const records = Array.from(this.state.analyses.values());
    const filtered = snapshotId
      ? records.filter((analysis) => analysis.snapshotId === snapshotId)
      : records;
    return filtered
      .slice()
      .sort((a, b) => {
        const aDate = a.createdAt ?? "";
        const bDate = b.createdAt ?? "";
        if (aDate === bDate) {
          return (b.id ?? 0) - (a.id ?? 0);
        }
        return aDate < bDate ? 1 : -1;
      })
      .map((analysis) => cloneAnalysis(analysis));
  }

  public create(input: CreateAnalysisInput): StoredAnalysis {
    const id = this.state.nextAnalysisId++;
    const createdAt = new Date().toISOString();
    const analysis: StoredAnalysis = {
      id,
      snapshotId: input.snapshotId,
      author: input.author,
      title: input.title,
      notes: input.notes ?? undefined,
      createdAt,
      items: [],
    };

    const items = input.items ?? [];
    for (const item of items) {
      const itemId = this.state.nextItemId++;
      analysis.items.push({
        id: itemId,
        analysisId: id,
        label: item.label,
        score: item.score,
        payload: item.payload,
      });
    }

    if (analysis.items.length === 0) {
      const placeholderId = this.state.nextItemId++;
      analysis.items.push({
        id: placeholderId,
        analysisId: id,
        label: "auto-generated",
        score: 0,
        payload: {
          id: randomUUID(),
          message: "No analysis items provided; generated placeholder entry.",
        },
      });
    }

    this.state.analyses.set(id, analysis);
    return cloneAnalysis(analysis);
  }
}

export function getAnalysisStore(): AnalysisStore {
  return getGlobalStore();
}
