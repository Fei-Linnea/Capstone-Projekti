"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { RunState } from "@/lib/types";
import { getStatus } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/**
 * Hook that provides live pipeline status.
 *
 * Connects to the SSE endpoint while the pipeline is running,
 * otherwise polls every few seconds to detect when a new run starts.
 */
export function usePipelineStatus() {
  const [state, setState] = useState<RunState | null>(null);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch status once (used by polling and initial load)
  const fetchStatus = useCallback(async () => {
    try {
      const s = await getStatus();
      setState(s);
      return s;
    } catch {
      return null;
    }
  }, []);

  // Connect to SSE stream
  const connectSSE = useCallback(() => {
    if (eventSourceRef.current) return;

    const es = new EventSource(`${API_BASE}/api/progress/stream`);
    eventSourceRef.current = es;

    es.addEventListener("status", (e) => {
      try {
        const data: RunState = JSON.parse(e.data);
        setState(data);
        setConnected(true);
      } catch {}
    });

    es.addEventListener("complete", (e) => {
      try {
        const data: RunState = JSON.parse(e.data);
        setState(data);
      } catch {}
      es.close();
      eventSourceRef.current = null;
      setConnected(false);
    });

    es.addEventListener("idle", (e) => {
      try {
        const data: RunState = JSON.parse(e.data);
        setState(data);
      } catch {}
      es.close();
      eventSourceRef.current = null;
      setConnected(false);
    });

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
      setConnected(false);
    };
  }, []);

  // Poll + auto-connect SSE when running
  useEffect(() => {
    // Initial fetch
    fetchStatus().then((s) => {
      if (s && (s.status === "running" || s.status === "cancelling")) {
        connectSSE();
      }
    });

    // Poll every 3s when not connected to SSE
    pollRef.current = setInterval(async () => {
      if (eventSourceRef.current) return; // SSE is active
      const s = await fetchStatus();
      if (s && (s.status === "running" || s.status === "cancelling")) {
        connectSSE();
      }
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [fetchStatus, connectSSE]);

  return { state, connected, refetch: fetchStatus };
}
