"use client";
import { useEffect, useState } from "react";
import type { DetectionModelInfo, DetectionStartRequest } from "@/types/detection";

export function DetectionControls({ model, disabled, onStart }: { model: DetectionModelInfo | null; disabled?: boolean; onStart: (payload: DetectionStartRequest) => void }) {
  const [confidence, setConfidence] = useState(0.35);
  const [batchSize, setBatchSize] = useState(8);
  const [mode, setMode] = useState<"sample" | "all">("sample");
  const [maxFrames, setMaxFrames] = useState(100);

  useEffect(() => {
    if (model) {
      setConfidence(model.confidence_default ?? 0.35);
      setBatchSize(model.batch_size_default ?? 8);
    }
  }, [model]);

  return (
    <section className="panel detection-controls">
      <div className="detection-controls-head">
        <p className="eyebrow">Object detection</p>
        <h2>YOLO frame inference</h2>
        <p>Runs actual model inference on extracted frames (Module 1). Detects <strong>person</strong> and <strong>sports ball</strong> only. No tracking or identity.</p>
        <dl className="metadata detection-meta-inline">
          <div><dt>Model</dt><dd>{model?.model_name ?? "Unavailable"}</dd></div>
          <div><dt>Device</dt><dd>{model?.device ?? "Unavailable"}</dd></div>
          <div><dt>Loaded</dt><dd>{model?.loaded ? "Yes (cached)" : "On demand"}</dd></div>
        </dl>
        {model?.detail && <p className="error">{model.detail}</p>}
      </div>
      <div className="detection-form">
        <label>Confidence threshold: {confidence.toFixed(2)}
          <input type="range" min={0.05} max={0.95} step={0.01} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} disabled={disabled} />
        </label>
        <label>Batch size
          <select value={batchSize} onChange={(e) => setBatchSize(Number(e.target.value))} disabled={disabled}>
            {[1,2,4,8,16,32].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <fieldset className="detection-mode">
          <legend>Processing scope</legend>
          <label><input type="radio" name="det-mode" checked={mode === "sample"} onChange={() => setMode("sample")} disabled={disabled} /> Test sample (recommended)</label>
          <label><input type="radio" name="det-mode" checked={mode === "all"} onChange={() => setMode("all")} disabled={disabled} /> Process all extracted frames</label>
          {mode === "sample" ? (
            <label>Max frames (sample)
              <input type="number" min={1} max={5000} value={maxFrames} onChange={(e) => setMaxFrames(Math.max(1, Number(e.target.value || 1)))} disabled={disabled} />
            </label>
          ) : <p className="muted-note">All available extracted frames will be processed. This may take a long time for full matches.</p>}
          <p className="muted-note">Test sample mode processes only a limited number of frames (default 100) so you can verify results before running full-video detection.</p>
        </fieldset>
        <button className="primary" type="button" disabled={disabled} onClick={() => onStart({ confidence_threshold: confidence, batch_size: batchSize, process_all_frames: mode === "all", max_frames: mode === "sample" ? maxFrames : null })}>
          {disabled ? "Detection running…" : "Start detection"}
        </button>
      </div>
    </section>
  );
}
