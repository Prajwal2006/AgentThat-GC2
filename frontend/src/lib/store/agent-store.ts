import { create } from "zustand";
import { Agent, apiGet, apiPost, apiPut } from "@/lib/api";

interface AgentState {
  agents: Agent[];
  loading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  createAgent: (name: string, description: string, category?: string) => Promise<Agent>;
  updateAgent: (id: string, data: Partial<Agent>) => Promise<void>;
  removeAgent: (id: string) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  loading: false,
  error: null,

  fetchAgents: async () => {
    set({ loading: true, error: null });
    try {
      const agents = await apiGet<Agent[]>("/v1/agents");
      set({ agents, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
  },

  createAgent: async (name, description, category = "General") => {
    const agent = await apiPost<Agent>("/v1/agents", { name, description, category });
    set((state) => ({ agents: [agent, ...state.agents] }));
    return agent;
  },

  updateAgent: async (id, data) => {
    const updated = await apiPut<Agent>(`/v1/agents/${id}`, data);
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, ...updated } : a)),
    }));
  },

  removeAgent: (id) => {
    set((state) => ({ agents: state.agents.filter((a) => a.id !== id) }));
  },
}));
