"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type DashboardStat = {
  title: string;
  value: string;
  change: string;
  icon: string;
};

export type Activity = {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  status: "active" | "success" | "pending" | string;
};

export type Agent = {
  id: string;
  name: string;
  description: string;
  status: string;
  usage: number;
  created: string;
  category: string;
};

export type WorkflowItem = {
  id: string;
  name: string;
  description: string;
  agents: number;
  status: string;
  lastRun: string;
};

export type MarketplaceItem = {
  id: string;
  name: string;
  creator: string;
  description: string;
  installs: number;
  rating: number;
  category: string;
  price: string;
  icon: string;
};

export type AnalyticsPoint = {
  month: string;
  adoption: number;
  efficiency: number;
  savings: number;
};

export type RoiMetric = {
  title: string;
  value: string;
  change: string;
  icon: string;
};

export type DepartmentMetric = {
  dept: string;
  adoption: number;
  users: number;
};

export type Course = {
  id: string;
  title: string;
  description: string;
  duration: string;
  lessons: number;
  completion: number;
  status: string;
};

export type LearningStat = {
  title: string;
  value: string;
  change: string;
  icon: string;
};

export type LearningPathItem = {
  step: number;
  title: string;
  status: string;
};

export type Certification = {
  name: string;
  courses: number;
  level: string;
};

export type PlatformOverview = {
  dashboardStats: DashboardStat[];
  recentActivity: Activity[];
  agents: Agent[];
};

export type AnalyticsResponse = {
  roiMetrics: RoiMetric[];
  series: AnalyticsPoint[];
  departments: DepartmentMetric[];
};

export type LearningResponse = {
  stats: LearningStat[];
  path: LearningPathItem[];
  courses: Course[];
  certifications: Certification[];
};

export type ProfileSettings = {
  full_name: string;
  email: string;
  role: "Admin" | "Developer" | "User";
};

export type NotificationItem = {
  label: string;
  enabled: boolean;
};

export type TeamMember = {
  id: string;
  name: string;
  role: "Admin" | "Developer" | "User";
  status: "Active" | "Invited";
};

export type DeploySolutionResponse = {
  status: "deployed";
  workflowId: string;
  agentsCreated: number;
  provider: "azure_openai" | "deterministic";
};

export type AiStatus = {
  provider: string;
  configured: boolean;
  deployment: string | null;
  apiVersion: string;
  mode: "live" | "deterministic-fallback";
};

export type ImprovePromptResponse = {
  original_prompt: string;
  improved_prompt: string;
  improvements: string[];
  provider: "azure_openai" | "deterministic";
};

export type AgentSpec = {
  name: string;
  purpose: string;
  prompt: string;
  tools: string[];
  handoff: string;
};

export type WorkflowStep = {
  id: string;
  name: string;
  agent: string;
  action: string;
  human_approval: boolean;
};

export type GeneratedSolution = {
  id: string;
  name: string;
  summary: string;
  improved_prompt: string;
  agents: AgentSpec[];
  workflow: WorkflowStep[];
  integrations: string[];
  governance: string[];
  observability: string[];
  deployment: Record<string, string>;
  provider: "azure_openai" | "deterministic";
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function useApiResource<T>(path: string, fallback: T) {
  const [data, setData] = useState<T>(fallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    apiGet<T>(path)
      .then((result) => {
        if (mounted) {
          setData(result);
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (mounted) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [path]);

  return { data, loading, error, setData };
}
