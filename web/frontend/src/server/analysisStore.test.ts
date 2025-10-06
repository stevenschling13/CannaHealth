import { beforeEach, describe, it } from "node:test";
import { AnalysisStore } from "./analysisStore.js";

function expect(condition: unknown, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

describe("AnalysisStore", () => {
  let store: AnalysisStore;

  beforeEach(() => {
    store = new AnalysisStore();
  });

  it("seeds an initial analysis", () => {
    const analyses = store.list();
    expect(analyses.length === 1, "expected exactly one seeded analysis");
    expect(
      analyses[0]?.title.includes("Initial"),
      "expected seeded analysis title to mention 'Initial'"
    );
  });

  it("creates new analyses with generated ids", () => {
    const created = store.create({
      snapshotId: 42,
      author: "QA",
      title: "Review",
    });
    expect((created.id ?? 0) > 1, "expected create to assign a unique id");
    expect(created.items.length > 0, "expected analysis to contain at least one item");

    const analyses = store.list();
    expect(
      analyses.some((analysis) => analysis.id === created.id),
      "expected created analysis to be discoverable in the list"
    );
  });

  it("filters by snapshot id", () => {
    store.create({
      snapshotId: 7,
      author: "QA",
      title: "Targeted",
    });

    const filtered = store.list(7);
    expect(filtered.length > 0, "expected at least one filtered analysis");
    expect(
      filtered.every((analysis) => analysis.snapshotId === 7),
      "expected all filtered analyses to match the snapshot id"
    );
  });
});
