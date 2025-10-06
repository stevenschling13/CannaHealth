import { useState } from "react";
import { createAnalysis } from "../lib/repository";

interface Props {
  snapshotId: number;
  onSaved?: () => void;
}

export function SaveAnalysisButton({ snapshotId, onSaved }: Props) {
  const [isSaving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleClick = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await createAnalysis({
        snapshotId,
        author: "dashboard-user",
        title: `Analysis for snapshot ${snapshotId}`,
        notes: "Triggered from the admin dashboard",
        items: [],
      });
      setMessage("Analysis saved successfully");
      onSaved?.();
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
      {message && <p role="status">{message}</p>}
    </div>
  );
}
