"use client";

import { useEffect, useRef, useState, useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface SSEEvent<T = unknown> {
  data: T;
  timestamp: number;
}

export interface UseSSEOptions {
  /** Auto-connect on mount */
  autoConnect?: boolean;
  /** Reconnect on error with exponential backoff */
  reconnect?: boolean;
  /** Max reconnect attempts (0 = infinite) */
  maxRetries?: number;
}

export interface UseSSEReturn<T> {
  data: T | null;
  events: SSEEvent<T>[];
  connected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for subscribing to Server-Sent Events (SSE) from the backend.
 * Used for job progress streaming and execution monitoring.
 */
export function useSSE<T = unknown>(
  path: string,
  options: UseSSEOptions = {}
): UseSSEReturn<T> {
  const { autoConnect = true, reconnect = true, maxRetries = 5 } = options;

  const [data, setData] = useState<T | null>(null);
  const [events, setEvents] = useState<SSEEvent<T>[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sourceRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);

  const disconnect = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    disconnect();
    setError(null);

    const url = `${API_BASE_URL}${path}`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onopen = () => {
      setConnected(true);
      setError(null);
      retriesRef.current = 0;
    };

    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        const sseEvent: SSEEvent<T> = {
          data: parsed,
          timestamp: Date.now(),
        };
        setData(parsed);
        setEvents((prev) => [...prev.slice(-99), sseEvent]);
      } catch {
        // Ignore non-JSON messages (heartbeats)
      }
    };

    source.onerror = () => {
      source.close();
      sourceRef.current = null;
      setConnected(false);

      if (reconnect && (maxRetries === 0 || retriesRef.current < maxRetries)) {
        retriesRef.current += 1;
        const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
        setError(`Connection lost. Retrying in ${Math.round(delay / 1000)}s...`);
        setTimeout(connect, delay);
      } else {
        setError("Connection closed");
      }
    };
  }, [path, disconnect, reconnect, maxRetries]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return { data, events, connected, error, connect, disconnect };
}

/**
 * Hook specifically for monitoring job progress via SSE.
 */
export function useJobProgress(jobId: string | null) {
  interface JobProgressData {
    job_id: string;
    progress_pct: number;
    status_message: string;
    status: string;
  }

  const result = useSSE<JobProgressData>(
    jobId ? `/v1/jobs/${jobId}/stream` : "",
    { autoConnect: !!jobId }
  );

  return {
    progress: result.data?.progress_pct ?? 0,
    statusMessage: result.data?.status_message ?? "",
    jobStatus: result.data?.status ?? "unknown",
    connected: result.connected,
    error: result.error,
  };
}

/**
 * Hook for monitoring execution progress via SSE.
 */
export function useExecutionStream(executionId: string | null) {
  interface ExecutionEvent {
    execution_id: string;
    step_index: number;
    total_steps: number;
    status: string;
    step_name: string;
    agent_id: string | null;
  }

  return useSSE<ExecutionEvent>(
    executionId ? `/v1/executions/${executionId}/stream` : "",
    { autoConnect: !!executionId }
  );
}
