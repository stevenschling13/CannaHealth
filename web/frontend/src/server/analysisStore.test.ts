import { describe, expect, it, beforeEach } from "vitest";
import { AnalysisStore } from "./analysisStore";

describe("AnalysisStore", () => {
  let store: AnalysisStore;

  beforeEach(() => {
    store = new AnalysisStore();
  });

  it("seeds an initial analysis", () => {
    const analyses = store.list();
    expect(analyses).toHaveLength(1);
    expect(analyses[0].title).toContain("Initial");
  });

  it("creates new analyses with generated ids", () => {
    const created = store.create({
      snapshotId: 42,
      author: "QA",
      title: "Review",
    });
    expect(created.id).toBeGreaterThan(1);
    expect(created.items.length).toBeGreaterThan(0);

    const analyses = store.list();
    expect(analyses.find((analysis) => analysis.id === created.id)).toBeDefined();
  });

  it("filters by snapshot id", () => {
    store.create({
      snapshotId: 7,
      author: "QA",
      title: "Targeted",
    });

    const filtered = store.list(7);
    expect(filtered.every((analysis) => analysis.snapshotId === 7)).toBe(true);
  });
});
