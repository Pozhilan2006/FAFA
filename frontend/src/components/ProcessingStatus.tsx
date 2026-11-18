"use client";

import { useState } from "react";
import type { ProcessingStatus as Status } from "@/types/video";

export function normaliseProgress(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

export function ProcessingStatus({ status, onStart }: { status: Status | null; onStart: (rate: number) => void }) {
  const [samplingFps, setSamplingFps] = useState("2");
  const active = status?.status === "processing" || status?.status === "queued";
  const progress = normaliseProgress(status?.progress_percentage);

  return (
    <section className="panel process">
      <div>
        <p className="eyebrow">Frame extraction</p>
        <h2>{status ? status.status : "Not started"}</h2>
        <p>{status ? `${status.frames_processed} extracted · ${status.frames_failed} failed` : "Select sampling FPS, then start processing."}</p>
        {status?.error_message && <p className="error">{status.error_message}</p>}
      </div>
      <div className="process-actions">
        <label>Sampling FPS
          <select disabled={active} value={samplingFps} onChange={(event) => setSamplingFps(event.target.value)}>
            <option value="1">1 FPS</option><option value="2">2 FPS</option><option value="5">5 FPS</option>
          </select>
        </label>
        <button className="primary" disabled={active} type="button" onClick={() => onStart(Number(samplingFps))}>
          {active ? "Processing…" : status?.status === "completed" ? "Process again" : "Extract frames"}
        </button>
      </div>
      {status && <div className="progress"><span style={{ width: `${progress}%` }} /><small>{progress.toFixed(1)}% {status.frames_expected ? `of ${status.frames_expected}` : ""}</small></div>}
    </section>
  );
}
