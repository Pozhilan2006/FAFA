import type { DetectionJob } from "@/types/detection";

function clamp(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

export function DetectionStatus({ job }: { job: DetectionJob | null }) {
  if (!job) return <section className="panel"><p className="eyebrow">Detection status</p><h2>Not started</h2><p>Configure detection and start a job to see progress and results.</p></section>;
  const progress = clamp(job.progress_percentage);
  return (
    <section className="panel">
      <p className="eyebrow">Detection status</p>
      <h2>{job.status}</h2>
      {job.error_message && <p className="error">{job.error_message}</p>}
      <dl className="metadata">
        <div><dt>Total frames</dt><dd>{job.total_frames ?? "Unknown"}</dd></div>
        <div><dt>Processed</dt><dd>{job.processed_frames}</dd></div>
        <div><dt>Failed</dt><dd>{job.failed_frames}</dd></div>
        <div><dt>Detections</dt><dd>{job.total_detections}</dd></div>
        <div><dt>Device</dt><dd>{job.processing_device ?? "Unknown"}</dd></div>
        <div><dt>Duration</dt><dd>{job.processing_duration_seconds != null ? `${job.processing_duration_seconds.toFixed(2)} s` : "—"}</dd></div>
      </dl>
      <div className="progress" style={{ marginTop: 16 }}><span style={{ width: `${progress}%` }} /><small>{progress.toFixed(1)}% {job.total_frames ? `of ${job.total_frames} frames` : ""}</small></div>
      <p className="muted-note">Job: {job.job_id} · Model: {job.model_name} · Confidence ≥ {job.confidence_threshold.toFixed(2)} · Batch {job.batch_size}</p>
    </section>
  );
}
