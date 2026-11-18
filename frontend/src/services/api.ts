import type { ExtractedFrame, FramePage, ProcessingStatus, VideoMetadata } from "@/types/video";
import type { DetectionFrameResult, DetectionJob, DetectionModelInfo, DetectionResultsPage, DetectionStartRequest, DetectionSummary } from "@/types/detection";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010";
const endpoint = (path: string) => `${baseUrl}/api${path}`;
const backendUrl = (path: string) => path.startsWith("http") ? path : `${baseUrl}${path}`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(endpoint(path), init);
  if (!response.ok) { const body = await response.json().catch(() => null); throw new Error(body?.detail ?? `Request failed (${response.status})`); }
  return response.json() as Promise<T>;
}
export const api = {
  upload(file: File) { const form = new FormData(); form.append("file", file); return request<{ video_id: string }>("/videos/upload", { method: "POST", body: form }); },
  listVideos: () => request<VideoMetadata[]>("/videos"),
  getVideo: (id: string) => request<VideoMetadata>(`/videos/${id}`),
  startProcessing: (id: string, samplingFps: number) => request<ProcessingStatus>(`/videos/${id}/process`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sampling_fps: samplingFps }) }),
  getStatus: (id: string) => request<ProcessingStatus>(`/videos/${id}/status`),
  async getFrames(id: string, offset = 0) { const page = await request<FramePage>(`/videos/${id}/frames?offset=${offset}&limit=24`); return { ...page, items: page.items.map((frame) => ({ ...frame, image_url: backendUrl(frame.image_url) })) }; },
  previewUrl: (id: string) => endpoint(`/videos/${id}/preview`),
  frameUrl: (id: string, frameId: string) => endpoint(`/videos/${id}/frames/${frameId}`),

  getDetectionModelInfo: () => request<DetectionModelInfo>("/detection/model-info"),
  startDetection: (videoId: string, payload: DetectionStartRequest) => request<DetectionJob>(`/detection/${videoId}/start`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }),
  getDetectionStatus: (videoId: string, jobId?: string) => request<DetectionJob>(`/detection/${videoId}/status${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ""}`),
  getDetectionSummary: (videoId: string, jobId?: string) => request<DetectionSummary>(`/detection/${videoId}/summary${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ""}`),
  async getDetectionResults(videoId: string, offset = 0, jobId?: string) {
    const q = new URLSearchParams({ offset: String(offset), limit: "12" });
    if (jobId) q.set("job_id", jobId);
    const page = await request<DetectionResultsPage>(`/detection/${videoId}/results?${q.toString()}`);
    return { ...page, items: page.items.map((item) => ({ ...item, original_image_url: backendUrl(item.original_image_url), annotated_image_url: item.annotated_image_url ? backendUrl(item.annotated_image_url) : null })) };
  },
  async getDetectionFrame(videoId: string, frameId: string, jobId?: string) {
    const q = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
    const item = await request<DetectionFrameResult>(`/detection/${videoId}/frames/${frameId}${q}`);
    return { ...item, original_image_url: backendUrl(item.original_image_url), annotated_image_url: item.annotated_image_url ? backendUrl(item.annotated_image_url) : null };
  },
  detectionAnnotatedUrl: (videoId: string, frameId: string, jobId?: string) => endpoint(`/detection/${videoId}/annotated/${frameId}${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ""}`),
};
