export type DetectionModelInfo = {
  model_name: string;
  model_path: string | null;
  device: string;
  loaded: boolean;
  class_names: Record<string, string> | null;
  supported_target_classes: string[];
  confidence_default: number;
  batch_size_default: number;
  detail?: string | null;
};

export type DetectionJob = {
  job_id: string;
  video_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  model_name: string;
  confidence_threshold: number;
  batch_size: number;
  total_frames: number | null;
  processed_frames: number;
  failed_frames: number;
  total_detections: number;
  processing_device: string | null;
  progress_percentage: number;
  processing_duration_seconds: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type DetectionSummary = {
  job_id: string;
  video_id: string;
  total_person_detections: number;
  total_sports_ball_detections: number;
  total_detections: number;
  frames_processed: number;
  frames_with_detections: number;
  frames_without_detections: number;
  failed_frames: number;
  average_confidence: number | null;
  inference_seconds: number | null;
  average_inference_seconds_per_frame: number | null;
  frames_per_second: number | null;
};

export type DetectionBBox = { x_min: number; y_min: number; x_max: number; y_max: number };

export type NormalizedBBox = { x_center: number; y_center: number; width: number; height: number };

export type DetectionRecord = {
  detection_id: string;
  video_id: string;
  frame_id: string;
  frame_number: number;
  timestamp_seconds: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: DetectionBBox;
  image_width: number;
  image_height: number;
  normalized_bbox: NormalizedBBox | null;
};

export type DetectionFrameResult = {
  frame_id: string;
  frame_number: number;
  timestamp_seconds: number;
  original_image_url: string;
  annotated_image_url: string | null;
  detection_count: number;
  detected_class_names: string[];
  detections: DetectionRecord[];
};

export type DetectionResultsPage = {
  items: DetectionFrameResult[];
  offset: number;
  limit: number;
  total: number;
};

export type DetectionStartRequest = {
  confidence_threshold: number;
  batch_size: number;
  max_frames?: number | null;
  process_all_frames: boolean;
};
