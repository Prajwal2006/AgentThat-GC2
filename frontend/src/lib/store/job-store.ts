import { create } from "zustand";
import { apiGet, apiPost } from "@/lib/api";

export interface JobProgress {
  job_id: string;
  progress_pct: number;
  status_message: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
}

interface JobState {
  activeJobs: Map<string, JobProgress>;
  subscribeToJob: (jobId: string) => void;
  unsubscribeFromJob: (jobId: string) => void;
  cancelJob: (jobId: string) => Promise<void>;
  getJobStatus: (jobId: string) => Promise<JobProgress | null>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

// Track active EventSource connections
const eventSources = new Map<string, EventSource>();

export const useJobStore = create<JobState>((set) => ({
  activeJobs: new Map(),

  subscribeToJob: (jobId: string) => {
    // Close existing connection if any
    const existing = eventSources.get(jobId);
    if (existing) existing.close();

    const source = new EventSource(`${API_BASE_URL}/v1/jobs/${jobId}/stream`);
    eventSources.set(jobId, source);

    source.onmessage = (event) => {
      try {
        const data: JobProgress = JSON.parse(event.data);
        set((state) => {
          const updated = new Map(state.activeJobs);
          updated.set(jobId, data);
          return { activeJobs: updated };
        });

        // Auto-close on terminal states
        if (["completed", "failed", "cancelled"].includes(data.status)) {
          source.close();
          eventSources.delete(jobId);
        }
      } catch {
        // Ignore parse errors (heartbeats)
      }
    };

    source.onerror = () => {
      source.close();
      eventSources.delete(jobId);
    };
  },

  unsubscribeFromJob: (jobId: string) => {
    const source = eventSources.get(jobId);
    if (source) {
      source.close();
      eventSources.delete(jobId);
    }
    set((state) => {
      const updated = new Map(state.activeJobs);
      updated.delete(jobId);
      return { activeJobs: updated };
    });
  },

  cancelJob: async (jobId: string) => {
    await apiPost(`/v1/jobs/${jobId}/cancel`, {});
    set((state) => {
      const updated = new Map(state.activeJobs);
      const job = updated.get(jobId);
      if (job) {
        updated.set(jobId, { ...job, status: "cancelled" });
      }
      return { activeJobs: updated };
    });
  },

  getJobStatus: async (jobId: string) => {
    try {
      const job = await apiGet<JobProgress>(`/v1/jobs/${jobId}`);
      set((state) => {
        const updated = new Map(state.activeJobs);
        updated.set(jobId, job);
        return { activeJobs: updated };
      });
      return job;
    } catch {
      return null;
    }
  },
}));
