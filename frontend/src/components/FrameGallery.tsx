"use client";

import { useState } from "react";
import type { ExtractedFrame, FramePage } from "@/types/video";

function FrameImage({ frame }: { frame: ExtractedFrame }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <div className="frame-image-fallback" role="img" aria-label={`Frame ${frame.frame_number} could not be loaded`}>Image unavailable</div>;
  return <img src={frame.image_url} alt={`Frame ${frame.frame_number}`} onError={() => setFailed(true)} />;
}

export function FrameGallery({ frames, onPage, onSelect }: { frames: FramePage | null; onPage: (offset: number) => void; onSelect: (url: string) => void }) {
  if (!frames) return <section className="panel"><h2>Extracted frames</h2><p>Processed frames will appear here once extraction begins.</p></section>;
  const page = Math.floor(frames.offset / frames.limit) + 1;
  return <section className="panel"><div className="gallery-heading"><div><p className="eyebrow">Frame gallery</p><h2>{frames.total} extracted frames</h2></div><div className="pager"><button disabled={frames.offset === 0} onClick={() => onPage(Math.max(0, frames.offset - frames.limit))}>Previous</button><span>Page {page}</span><button disabled={frames.offset + frames.limit >= frames.total} onClick={() => onPage(frames.offset + frames.limit)}>Next</button></div></div><div className="gallery">{frames.items.map((frame) => <button className="frame" key={frame.frame_id} onClick={() => onSelect(frame.image_url)}><FrameImage frame={frame} /><span>#{frame.frame_number} · {frame.timestamp_seconds.toFixed(3)}s</span><small>{frame.processed_width}×{frame.processed_height}</small></button>)}</div></section>;
}
