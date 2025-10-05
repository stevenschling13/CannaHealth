export interface StoredAnalysisItem {
  id?: number;
  label: string;
  score: number;
  payload?: unknown;
}

export interface StoredAnalysis {
  id?: number;
  snapshotId: number;
  author: string;
  title: string;
  notes?: string;
  createdAt?: string;
  items: StoredAnalysisItem[];
}

const DB_NAME = "canna-health";
const DB_VERSION = 1;
const ANALYSIS_STORE = "analysis";

export async function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(ANALYSIS_STORE)) {
        db.createObjectStore(ANALYSIS_STORE, { keyPath: "id", autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveAnalysis(analysis: StoredAnalysis): Promise<number> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(ANALYSIS_STORE, "readwrite");
    const store = tx.objectStore(ANALYSIS_STORE);
    const request = store.put(analysis);
    request.onsuccess = () => resolve(request.result as number);
    request.onerror = () => reject(request.error);
  });
}

export async function listAnalysis(): Promise<StoredAnalysis[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(ANALYSIS_STORE, "readonly");
    const store = tx.objectStore(ANALYSIS_STORE);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result as StoredAnalysis[]);
    request.onerror = () => reject(request.error);
  });
}
