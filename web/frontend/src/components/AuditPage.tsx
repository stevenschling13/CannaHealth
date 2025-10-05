"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchAnalysis } from "../lib/repository";
import type { StoredAnalysis } from "../lib/db";
import { SaveAnalysisButton } from "./SaveAnalysisButton";

export function AuditPage() {
  const [analyses, setAnalyses] = useState<StoredAnalysis[]>([]);
  const [isLoading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalyses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAnalysis();
      setAnalyses(data);
    } catch (err) {
      console.error(err);
      setError("Unable to load analyses");
      setAnalyses([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalyses();
  }, [loadAnalyses]);

  return (
    <section>
      <h1>Audit trail</h1>
      <SaveAnalysisButton snapshotId={1} onSaved={loadAnalyses} />
      {isLoading && <p>Loading analyses…</p>}
      {error && <p role="alert">{error}</p>}
      <ul>
        {analyses.map((analysis) => (
          <li key={analysis.id ?? `${analysis.snapshotId}-${analysis.title}`}
              data-testid="analysis-row">
            <strong>{analysis.title}</strong> by {analysis.author}
            {analysis.createdAt && (
              <span> — {new Date(analysis.createdAt).toLocaleString()}</span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default AuditPage;
