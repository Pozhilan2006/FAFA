"use client";
import { useState } from "react";
import type { DetectionFrameResult, DetectionResultsPage } from "@/types/detection";

export function DetectionResults({ results, onPage, onSelect }: { results: DetectionResultsPage | null; onPage: (offset: number) => void; onSelect: (item: DetectionFrameResult) => void }) {
  if (!results) return <section className="panel"><p className="eyebrow">Detection results</p><h2>Annotated frames</h2><p>Detection results will appear here after a job completes.</p></section>;
  const page = Math.floor(results.offset / results.limit) + 1;
  return (
    <section className="panel">
      <div className="gallery-heading">
        <div><p className="eyebrow">Detection results</p><h2>{results.total} processed frames</h2></div>
        <div className="pager">
          <button className="pager-btn" disabled={results.offset === 0} onClick={() => onPage(Math.max(0, results.offset - results.limit))}>Previous</button>
          <span>Page {page}</span>
          <button className="pager-btn" disabled={results.offset + results.limit >= results.total} onClick={() => onPage(results.offset + results.limit)}>Next</button>
        </div>
      </div>
      {results.items.length === 0 ? <p className="muted-note">No annotated frames for this job yet.</p> : (
        <div className="gallery detection-gallery">
          {results.items.map((item) => (
            <button className="frame detection-card" key={item.frame_id} onClick={() => onSelect(item)}>
              {item.annotated_image_url ? <img src={item.annotated_image_url} alt={`Annotated frame ${item.frame_number}`} /> : <div className="frame-image-fallback">No image</div>}
              <span>#{item.frame_number} · {item.timestamp_seconds.toFixed(3)}s</span>
              <small>{item.detection_count} detections · {item.detected_class_names.join(", ") || "none"}</small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
