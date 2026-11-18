"use client";
import { useEffect, useState } from "react";
import { FrameGallery } from "@/components/FrameGallery";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { VideoMetadata } from "@/components/VideoMetadata";
import { VideoPreview } from "@/components/VideoPreview";
import { VideoUploader } from "@/components/VideoUploader";
import { DetectionControls } from "@/components/detection/DetectionControls";
import { DetectionImage } from "@/components/detection/DetectionImage";
import { DetectionResults } from "@/components/detection/DetectionResults";
import { DetectionStatus } from "@/components/detection/DetectionStatus";
import { DetectionSummary } from "@/components/detection/DetectionSummary";
import { api } from "@/services/api";
import type { DetectionFrameResult, DetectionJob, DetectionModelInfo, DetectionResultsPage, DetectionStartRequest, DetectionSummary as DetectionSummaryType } from "@/types/detection";
import type { FramePage, ProcessingStatus as Status, VideoMetadata as Video } from "@/types/video";

export default function DashboardPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [video, setVideo] = useState<Video | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [frames, setFrames] = useState<FramePage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<string | null>(null);

  const [detModel, setDetModel] = useState<DetectionModelInfo | null>(null);
  const [detJob, setDetJob] = useState<DetectionJob | null>(null);
  const [detSummary, setDetSummary] = useState<DetectionSummaryType | null>(null);
  const [detResults, setDetResults] = useState<DetectionResultsPage | null>(null);
  const [detFrame, setDetFrame] = useState<DetectionFrameResult | null>(null);

  const refreshVideos = async () => {
    try { setVideos(await api.listVideos()); } catch {}
  };

  const loadFrames = async (id: string, offset = 0) => {
    try { setFrames(await api.getFrames(id, offset)); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load frames."); }
  };
  const loadStatus = async (id: string) => {
    try {
      const next = await api.getStatus(id);
      setStatus(next);
      if (next.status === "completed") await loadFrames(id);
    } catch {}
  };

  const loadDetection = async (id: string, jobId?: string) => {
    try {
      const job = await api.getDetectionStatus(id, jobId);
      setDetJob(job);
      if (job.status === "completed") {
        try { setDetSummary(await api.getDetectionSummary(id, job.job_id)); } catch {}
        try { setDetResults(await api.getDetectionResults(id, 0, job.job_id)); } catch {}
      } else {
        setDetSummary(null);
        setDetResults(null);
      }
    } catch {
      setDetJob(null); setDetSummary(null); setDetResults(null);
    }
  };

  useEffect(() => { void refreshVideos(); void api.getDetectionModelInfo().then(setDetModel).catch(() => {}); }, []);

  useEffect(() => {
    if (!video) return;
    void loadStatus(video.video_id);
    void loadFrames(video.video_id);
    void loadDetection(video.video_id);
  }, [video?.video_id]);

  useEffect(() => {
    if (!video || !status || !["queued", "processing"].includes(status.status)) return;
    const timer = window.setInterval(() => void loadStatus(video.video_id), 1500);
    return () => window.clearInterval(timer);
  }, [video?.video_id, status?.status]);

  useEffect(() => {
    if (!video || !detJob || !["queued", "processing"].includes(detJob.status)) return;
    const timer = window.setInterval(() => void loadDetection(video.video_id, detJob.job_id), 2000);
    return () => window.clearInterval(timer);
  }, [video?.video_id, detJob?.status, detJob?.job_id]);

  const selectVideo = async (v: Video) => {
    setVideo(v); setError(null); setModal(null); setDetFrame(null);
  };

  const upload = async (file: File) => {
    const result = await api.upload(file);
    const next = await api.getVideo(result.video_id);
    setVideo(next); setStatus(null); setFrames(null); setError(null);
    setDetJob(null); setDetSummary(null); setDetResults(null); setDetFrame(null);
    await refreshVideos();
  };

  const startDetection = async (payload: DetectionStartRequest) => {
    if (!video) return;
    try {
      setError(null);
      const job = await api.startDetection(video.video_id, payload);
      setDetJob(job); setDetSummary(null); setDetResults(null); setDetFrame(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to start detection.");
    }
  };

  const detectionBusy = detJob?.status === "queued" || detJob?.status === "processing";

  return (
    <section className="dashboard">
      <header>
        <p className="eyebrow">Match workspace / Module 01 + 02</p>
        <h1>Turn the first whistle into a usable timeline.</h1>
        <p className="lead">Upload match footage, extract sampled frames, then run YOLO object detection to inspect person and football bounding boxes.</p>
      </header>
      {error && <p className="error" role="alert">{error}</p>}

      <VideoUploader onUpload={upload} />

      {videos.length > 0 && (
        <section className="panel">
          <p className="eyebrow">Uploaded videos (Module 1)</p>
          <h2>Select a video</h2>
          <div className="video-list">
            {videos.map((v) => (
              <button key={v.video_id} type="button" className={`video-pick ${video?.video_id === v.video_id ? "active" : ""}`} onClick={() => void selectVideo(v)}>
                <strong>{v.original_filename}</strong>
                <span>{v.format.toUpperCase()} · {v.duration_seconds ? `${v.duration_seconds.toFixed(1)}s` : "duration n/a"} · {v.upload_status}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {video && <>
        <VideoPreview video={video} url={api.previewUrl(video.video_id)} />
        <VideoMetadata video={video} />

        <section className="module-block">
          <h2 className="module-title">Module 1 — Frame extraction</h2>
          <ProcessingStatus status={status} onStart={async (rate) => { try { setStatus(await api.startProcessing(video.video_id, rate)); setError(null); } catch (e) { setError(e instanceof Error ? e.message : "Unable to start processing."); } }} />
          <FrameGallery frames={frames} onPage={(page) => void loadFrames(video.video_id, page)} onSelect={setModal} />
        </section>

        <section className="module-block">
          <h2 className="module-title">Module 2 — Object detection</h2>
          <DetectionControls model={detModel} disabled={detectionBusy} onStart={(p) => void startDetection(p)} />
          <DetectionStatus job={detJob} />
          <DetectionSummary summary={detSummary} />
          <DetectionResults
            results={detResults}
            onPage={(offset) => void api.getDetectionResults(video.video_id, offset, detJob?.job_id).then(setDetResults).catch((e) => setError(e instanceof Error ? e.message : "Unable to load detection results."))}
            onSelect={(item) => void api.getDetectionFrame(video.video_id, item.frame_id, detJob?.job_id).then(setDetFrame).catch(() => setDetFrame(item))}
          />
        </section>
      </>}

      {modal && <dialog open className="frame-modal" onClick={() => setModal(null)}><img src={modal} alt="Full extracted frame" /></dialog>}
      {detFrame && <DetectionImage item={detFrame} onClose={() => setDetFrame(null)} />}
    </section>
  );
}
