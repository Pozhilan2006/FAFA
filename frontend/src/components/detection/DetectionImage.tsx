import type { DetectionFrameResult } from "@/types/detection";

export function DetectionImage({ item, onClose }: { item: DetectionFrameResult; onClose: () => void }) {
  return (
    <dialog open className="frame-modal detection-modal" onClick={onClose}>
      <div className="detection-modal-inner" onClick={(e) => e.stopPropagation()}>
        <div className="detection-modal-head">
          <div>
            <p className="eyebrow">Frame {item.frame_number} · {item.timestamp_seconds.toFixed(3)}s</p>
            <h3>{item.detection_count} detection{item.detection_count === 1 ? "" : "s"}</h3>
          </div>
          <button type="button" className="pager-btn" onClick={onClose}>Close</button>
        </div>
        <div className="detection-compare">
          <figure>
            <img src={item.original_image_url} alt={`Original frame ${item.frame_number}`} />
            <figcaption>Original frame</figcaption>
          </figure>
          <figure>
            {item.annotated_image_url ? <img src={item.annotated_image_url} alt={`Annotated frame ${item.frame_number}`} /> : <div className="frame-image-fallback">Annotated image unavailable</div>}
            <figcaption>Annotated detections</figcaption>
          </figure>
        </div>
        <div className="detection-detail-list">
          {item.detections.length === 0 ? <p className="muted-note">No detections for this frame at the configured threshold.</p> : (
            <table className="detection-table">
              <thead><tr><th>ID</th><th>Class</th><th>Conf</th><th>BBox (x_min,y_min,x_max,y_max)</th></tr></thead>
              <tbody>
                {item.detections.map((d) => (
                  <tr key={d.detection_id}>
                    <td title={d.detection_id}>{d.detection_id.slice(0, 8)}</td>
                    <td>{d.class_name} ({d.class_id})</td>
                    <td>{(d.confidence * 100).toFixed(1)}%</td>
                    <td>[{d.bbox.x_min.toFixed(1)}, {d.bbox.y_min.toFixed(1)}, {d.bbox.x_max.toFixed(1)}, {d.bbox.y_max.toFixed(1)}]</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </dialog>
  );
}
