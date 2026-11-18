import type { DetectionSummary as Summary } from "@/types/detection";

export function DetectionSummary({ summary }: { summary: Summary | null }) {
  if (!summary) return null;
  return (
    <section className="panel">
      <p className="eyebrow">Detection summary</p>
      <h2>Actual model results</h2>
      <dl className="metadata">
        <div><dt>Person detections</dt><dd>{summary.total_person_detections}</dd></div>
        <div><dt>Sports-ball detections</dt><dd>{summary.total_sports_ball_detections}</dd></div>
        <div><dt>Total detections</dt><dd>{summary.total_detections}</dd></div>
        <div><dt>Frames processed</dt><dd>{summary.frames_processed}</dd></div>
        <div><dt>With detections</dt><dd>{summary.frames_with_detections}</dd></div>
        <div><dt>Without detections</dt><dd>{summary.frames_without_detections}</dd></div>
        <div><dt>Failed frames</dt><dd>{summary.failed_frames}</dd></div>
        <div><dt>Avg confidence</dt><dd>{summary.average_confidence != null ? summary.average_confidence.toFixed(3) : "—"}</dd></div>
        <div><dt>Inference time</dt><dd>{summary.inference_seconds != null ? `${summary.inference_seconds.toFixed(2)} s` : "—"}</dd></div>
        <div><dt>Avg / frame</dt><dd>{summary.average_inference_seconds_per_frame != null ? `${summary.average_inference_seconds_per_frame.toFixed(4)} s` : "—"}</dd></div>
        <div><dt>Frames / sec</dt><dd>{summary.frames_per_second != null ? summary.frames_per_second.toFixed(3) : "—"}</dd></div>
      </dl>
    </section>
  );
}
