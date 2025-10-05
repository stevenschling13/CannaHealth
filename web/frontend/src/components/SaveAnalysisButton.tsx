import { useState } from "react";
import { createAnalysis } from "../lib/repository";

interface Props {
  snapshotId: number;
}

export function SaveAnalysisButton({ snapshotId }: Props) {
  const [isSaving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleClick = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await createAnalysis({
        snapshotId,
        author: "local-user",
        title: "Quick analysis",
        items: [],
      });
      setMessage("Saved analysis to IndexedDB");
    } catch (error) {
      console.error(error);
      setMessage("Failed to save analysis");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <button onClick={handleClick} disabled={isSaving}>
        {isSaving ? "Saving..." : "Save analysis"}
      </button>
      {message && <p>{message}</p>}
    </div>
  );
}
