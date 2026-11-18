"use client";
import { useRef, useState } from "react";

export function VideoUploader({ onUpload }: { onUpload: (file: File) => Promise<void> }) {
  const input = useRef<HTMLInputElement>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  const submit = async (file?: File) => { if (!file) return; setError(null); setBusy(true); try { await onUpload(file); } catch (e) { setError(e instanceof Error ? e.message : "Upload failed."); } finally { setBusy(false); } };
  return <section className="uploader" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); void submit(e.dataTransfer.files[0]); }}><input ref={input} type="file" accept=".mp4,.mov,.avi,video/mp4,video/quicktime,video/x-msvideo" hidden onChange={(e) => void submit(e.target.files?.[0])} /><p className="eyebrow">Video ingestion</p><h2>Start with match footage.</h2><p>MP4, MOV, or AVI. The backend validates the file content before storing it.</p><button className="primary" type="button" disabled={busy} onClick={() => input.current?.click()}>{busy ? "Uploading…" : "Select video"}</button>{error && <p className="error" role="alert">{error}</p>}</section>;
}
