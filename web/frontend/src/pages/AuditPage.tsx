import { useEffect, useState } from "react";
import { fetchAnalysis } from "../lib/repository";
import type { StoredAnalysis } from "../lib/db";
import { SaveAnalysisButton } from "../components/SaveAnalysisButton";

export function AuditPage() {
  const [analyses, setAnalyses] = useState<StoredAnalysis[]>([]);

  useEffect(() => {
    fetchAnalysis().then(setAnalyses).catch(() => setAnalyses([]));
  }, []);

  return (
    <section>
      <h1>Audit trail</h1>
      <SaveAnalysisButton snapshotId={1} />
      <ul>
        {analyses.map((analysis) => (
          <li key={analysis.id}>
            <strong>{analysis.title}</strong> by {analysis.author}
          </li>
        ))}
      </ul>
    </section>
  );
}
