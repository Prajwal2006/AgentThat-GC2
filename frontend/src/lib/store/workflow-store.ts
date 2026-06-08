import { create } from "zustand";
import { WorkflowItem, apiGet, apiPost } from "@/lib/api";

interface WorkflowState {
  workflows: WorkflowItem[];
  loading: boolean;
  error: string | null;
  fetchWorkflows: () => Promise<void>;
  createWorkflow: (name: string, description: string, agents?: number) => Promise<WorkflowItem>;
  controlWorkflow: (id: string, action: "run" | "pause" | "resume") => Promise<void>;
  removeWorkflow: (id: string) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  loading: false,
  error: null,

  fetchWorkflows: async () => {
    set({ loading: true, error: null });
    try {
      const workflows = await apiGet<WorkflowItem[]>("/v1/workflows");
      set({ workflows, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },

  createWorkflow: async (name, description, agents = 2) => {
    const workflow = await apiPost<WorkflowItem>("/v1/workflows", {
      name,
      description,
      agents,
    });
    set((state) => ({ workflows: [workflow, ...state.workflows] }));
    return workflow;
  },

  controlWorkflow: async (id, action) => {
    const updated = await apiPost<WorkflowItem>(`/v1/workflows/${id}/control`, {
      action,
    });
    set((state) => ({
      workflows: state.workflows.map((w) => (w.id === id ? updated : w)),
    }));
  },

  removeWorkflow: (id) => {
    set((state) => ({ workflows: state.workflows.filter((w) => w.id !== id) }));
  },
}));
