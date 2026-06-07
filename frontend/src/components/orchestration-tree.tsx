"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  Globe,
  Settings2,
  ClipboardList,
  Code2,
  Plus,
  Trash2,
  Database,
  Server,
  ChevronDown,
  ChevronRight,
  Zap,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

export type AgentRole =
  | "orchestrator"
  | "specialist"
  | "reviewer"
  | "worker"
  | "custom";

export interface AgentNode {
  id: string;
  name: string;
  model: string;
  role: AgentRole;
  icon: AgentRole;
  status: "active" | "idle" | "error" | "disabled";
  children: AgentNode[];
  knowledgeBases?: string[];
  mcpServers?: string[];
  tools?: string[];
}

export interface KnowledgeBase {
  id: string;
  name: string;
  type: "vector" | "document" | "api" | "database";
  status: "connected" | "disconnected" | "syncing";
}

export interface MCPServerConfig {
  id: string;
  name: string;
  url: string;
  status: "active" | "inactive" | "error";
  tools: string[];
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ROLE_ICONS: Record<AgentRole, React.ReactNode> = {
  orchestrator: <Home className="w-4 h-4" />,
  specialist: <Globe className="w-4 h-4" />,
  reviewer: <ClipboardList className="w-4 h-4" />,
  worker: <Code2 className="w-4 h-4" />,
  custom: <Settings2 className="w-4 h-4" />,
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-emerald-400",
  idle: "bg-amber-400",
  error: "bg-red-400",
  disabled: "bg-gray-500",
  connected: "bg-emerald-400",
  disconnected: "bg-gray-500",
  syncing: "bg-amber-400",
  inactive: "bg-gray-500",
};

// ─── Tree Node Component ──────────────────────────────────────────────────────

function TreeNode({
  node,
  level,
  isLast,
  onSelect,
  selectedId,
  onAddChild,
  onRemove,
}: {
  node: AgentNode;
  level: number;
  isLast: boolean;
  onSelect: (id: string) => void;
  selectedId: string | null;
  onAddChild: (parentId: string) => void;
  onRemove: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children.length > 0;

  return (
    <div className="relative">
      {/* Vertical connector from parent */}
      {level > 0 && (
        <div
          className="absolute top-0 left-[-24px] w-[1px] bg-border"
          style={{ height: isLast ? "24px" : "100%" }}
        />
      )}
      {/* Horizontal connector */}
      {level > 0 && (
        <div className="absolute top-[24px] left-[-24px] w-[24px] h-[1px] bg-border" />
      )}

      {/* Node Card */}
      <motion.div
        layout
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className={cn(
          "relative flex items-center gap-3 px-4 py-3 rounded-xl border cursor-pointer transition-all select-none",
          "hover:border-accent/50 hover:shadow-md hover:shadow-accent/5",
          isSelected
            ? "border-emerald-400 bg-emerald-400/5 shadow-lg shadow-emerald-400/10"
            : "border-border bg-card"
        )}
        onClick={() => onSelect(node.id)}
      >
        {/* Status badge */}
        {isSelected && (
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute -top-2 left-4 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-400 text-black"
          >
            Active
          </motion.span>
        )}

        {/* Expand/collapse toggle */}
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="text-muted-foreground hover:text-foreground"
          >
            {expanded ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>
        )}

        {/* Icon */}
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-secondary border border-border">
          {ROLE_ICONS[node.role]}
        </div>

        {/* Label */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate">{node.name}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className={cn("w-2 h-2 rounded-full", STATUS_COLORS[node.status])}
            />
            <span className="text-xs text-muted-foreground">{node.model}</span>
          </div>
        </div>

        {/* Indicators */}
        <div className="flex items-center gap-1.5">
          {node.knowledgeBases && node.knowledgeBases.length > 0 && (
            <span className="text-xs text-muted-foreground flex items-center gap-0.5">
              <BookOpen className="w-3 h-3" />
              {node.knowledgeBases.length}
            </span>
          )}
          {node.mcpServers && node.mcpServers.length > 0 && (
            <span className="text-xs text-muted-foreground flex items-center gap-0.5">
              <Server className="w-3 h-3" />
              {node.mcpServers.length}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddChild(node.id);
            }}
            className="p-1 rounded hover:bg-accent/20 text-muted-foreground hover:text-accent"
            title="Add child agent"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          {level > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(node.id);
              }}
              className="p-1 rounded hover:bg-red-500/20 text-muted-foreground hover:text-red-400"
              title="Remove agent"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </motion.div>

      {/* Children */}
      <AnimatePresence>
        {expanded && hasChildren && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="pl-12 mt-3 space-y-3 relative"
          >
            {/* Vertical line connecting children */}
            <div className="absolute top-0 left-[24px] w-[1px] h-full bg-border" />
            {node.children.map((child, idx) => (
              <TreeNode
                key={child.id}
                node={child}
                level={level + 1}
                isLast={idx === node.children.length - 1}
                onSelect={onSelect}
                selectedId={selectedId}
                onAddChild={onAddChild}
                onRemove={onRemove}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Side Panel Components ────────────────────────────────────────────────────

function KnowledgeBasePanel({
  knowledgeBases,
  selectedAgent,
  onAttach,
  onDetach,
}: {
  knowledgeBases: KnowledgeBase[];
  selectedAgent: AgentNode | null;
  onAttach: (agentId: string, kbId: string) => void;
  onDetach: (agentId: string, kbId: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Database className="w-4 h-4 text-accent" />
        Knowledge Bases
      </div>
      <div className="space-y-2">
        {knowledgeBases.map((kb) => {
          const isAttached = selectedAgent?.knowledgeBases?.includes(kb.id);
          return (
            <div
              key={kb.id}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all",
                isAttached
                  ? "border-accent/50 bg-accent/5"
                  : "border-border bg-card hover:border-border/80"
              )}
            >
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  STATUS_COLORS[kb.status]
                )}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{kb.name}</p>
                <p className="text-[10px] text-muted-foreground">{kb.type}</p>
              </div>
              {selectedAgent && (
                <button
                  onClick={() =>
                    isAttached
                      ? onDetach(selectedAgent.id, kb.id)
                      : onAttach(selectedAgent.id, kb.id)
                  }
                  className={cn(
                    "px-2 py-0.5 text-[10px] font-medium rounded-full border transition-colors",
                    isAttached
                      ? "border-red-400/50 text-red-400 hover:bg-red-400/10"
                      : "border-accent/50 text-accent hover:bg-accent/10"
                  )}
                >
                  {isAttached ? "Detach" : "Attach"}
                </button>
              )}
            </div>
          );
        })}
      </div>
      <Button variant="ghost" size="sm" className="w-full gap-2 text-xs">
        <Plus className="w-3 h-3" />
        Add Knowledge Base
      </Button>
    </div>
  );
}

function MCPServerPanel({
  mcpServers,
  selectedAgent,
  onAttach,
  onDetach,
}: {
  mcpServers: MCPServerConfig[];
  selectedAgent: AgentNode | null;
  onAttach: (agentId: string, serverId: string) => void;
  onDetach: (agentId: string, serverId: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Server className="w-4 h-4 text-primary" />
        MCP Servers
      </div>
      <div className="space-y-2">
        {mcpServers.map((server) => {
          const isAttached = selectedAgent?.mcpServers?.includes(server.id);
          return (
            <div
              key={server.id}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all",
                isAttached
                  ? "border-primary/50 bg-primary/5"
                  : "border-border bg-card hover:border-border/80"
              )}
            >
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  STATUS_COLORS[server.status]
                )}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{server.name}</p>
                <p className="text-[10px] text-muted-foreground">
                  {server.tools.length} tools
                </p>
              </div>
              {selectedAgent && (
                <button
                  onClick={() =>
                    isAttached
                      ? onDetach(selectedAgent.id, server.id)
                      : onAttach(selectedAgent.id, server.id)
                  }
                  className={cn(
                    "px-2 py-0.5 text-[10px] font-medium rounded-full border transition-colors",
                    isAttached
                      ? "border-red-400/50 text-red-400 hover:bg-red-400/10"
                      : "border-primary/50 text-primary hover:bg-primary/10"
                  )}
                >
                  {isAttached ? "Detach" : "Attach"}
                </button>
              )}
            </div>
          );
        })}
      </div>
      <Button variant="ghost" size="sm" className="w-full gap-2 text-xs">
        <Plus className="w-3 h-3" />
        Add MCP Server
      </Button>
    </div>
  );
}

// ─── Agent Detail Panel ───────────────────────────────────────────────────────

function AgentDetailPanel({ agent }: { agent: AgentNode }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-secondary border border-border">
          {ROLE_ICONS[agent.role]}
        </div>
        <div>
          <p className="text-sm font-semibold">{agent.name}</p>
          <p className="text-xs text-muted-foreground">{agent.model}</p>
        </div>
        <Badge
          variant={agent.status === "active" ? "default" : "info"}
          className="ml-auto text-[10px]"
        >
          {agent.status}
        </Badge>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Configuration
        </p>
        <div className="grid grid-cols-2 gap-2">
          <div className="px-3 py-2 rounded-lg bg-secondary border border-border">
            <p className="text-[10px] text-muted-foreground">Role</p>
            <p className="text-xs font-medium capitalize">{agent.role}</p>
          </div>
          <div className="px-3 py-2 rounded-lg bg-secondary border border-border">
            <p className="text-[10px] text-muted-foreground">Children</p>
            <p className="text-xs font-medium">{agent.children.length}</p>
          </div>
        </div>
      </div>

      {agent.tools && agent.tools.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Tools
          </p>
          <div className="flex flex-wrap gap-1.5">
            {agent.tools.map((tool) => (
              <span
                key={tool}
                className="px-2 py-0.5 text-[10px] rounded-full bg-accent/10 border border-accent/20 text-accent"
              >
                {tool}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Orchestration Tree Component ────────────────────────────────────────

const DEFAULT_TREE: AgentNode = {
  id: "root",
  name: "CEO Agent",
  model: "GPT-4o",
  role: "orchestrator",
  icon: "orchestrator",
  status: "active",
  knowledgeBases: ["kb-1"],
  mcpServers: ["mcp-1"],
  tools: ["Audit Log", "Human Approval"],
  children: [
    {
      id: "marketing",
      name: "Marketing Agent",
      model: "GPT-4o",
      role: "specialist",
      icon: "specialist",
      status: "active",
      knowledgeBases: ["kb-2"],
      mcpServers: [],
      tools: ["Content Gen", "Analytics"],
      children: [],
    },
    {
      id: "engineering",
      name: "Engineering Lead",
      model: "Claude 3.5",
      role: "specialist",
      icon: "specialist",
      status: "idle",
      knowledgeBases: [],
      mcpServers: ["mcp-2"],
      tools: ["GitHub", "Jira", "Code Review"],
      children: [
        {
          id: "frontend",
          name: "Frontend Engineer",
          model: "Cursor",
          role: "worker",
          icon: "worker",
          status: "idle",
          knowledgeBases: [],
          mcpServers: [],
          tools: ["React", "CSS", "Testing"],
          children: [],
        },
        {
          id: "backend",
          name: "Backend Engineer",
          model: "Claude 3.5",
          role: "worker",
          icon: "worker",
          status: "idle",
          knowledgeBases: ["kb-1"],
          mcpServers: ["mcp-1"],
          tools: ["Python", "SQL", "API Design"],
          children: [],
        },
      ],
    },
    {
      id: "operations",
      name: "Operations Agent",
      model: "GPT-4o-mini",
      role: "reviewer",
      icon: "reviewer",
      status: "idle",
      knowledgeBases: ["kb-3"],
      mcpServers: [],
      tools: ["Scheduling", "Reports"],
      children: [],
    },
  ],
};

const DEFAULT_KNOWLEDGE_BASES: KnowledgeBase[] = [
  { id: "kb-1", name: "Enterprise Docs", type: "vector", status: "connected" },
  { id: "kb-2", name: "Marketing Assets", type: "document", status: "connected" },
  { id: "kb-3", name: "Operations Playbook", type: "document", status: "syncing" },
  { id: "kb-4", name: "Product API", type: "api", status: "disconnected" },
];

const DEFAULT_MCP_SERVERS: MCPServerConfig[] = [
  {
    id: "mcp-1",
    name: "Database Tools",
    url: "localhost:3001",
    status: "active",
    tools: ["query", "insert", "update", "schema"],
  },
  {
    id: "mcp-2",
    name: "GitHub Integration",
    url: "localhost:3002",
    status: "active",
    tools: ["create_pr", "review_code", "merge", "issues"],
  },
  {
    id: "mcp-3",
    name: "Slack Connector",
    url: "localhost:3003",
    status: "inactive",
    tools: ["send_message", "create_channel", "search"],
  },
];

// ─── Helper functions ─────────────────────────────────────────────────────────

function findNode(tree: AgentNode, id: string): AgentNode | null {
  if (tree.id === id) return tree;
  for (const child of tree.children) {
    const found = findNode(child, id);
    if (found) return found;
  }
  return null;
}

function addChildToNode(tree: AgentNode, parentId: string, child: AgentNode): AgentNode {
  if (tree.id === parentId) {
    return { ...tree, children: [...tree.children, child] };
  }
  return {
    ...tree,
    children: tree.children.map((c) => addChildToNode(c, parentId, child)),
  };
}

function removeNodeFromTree(tree: AgentNode, nodeId: string): AgentNode {
  return {
    ...tree,
    children: tree.children
      .filter((c) => c.id !== nodeId)
      .map((c) => removeNodeFromTree(c, nodeId)),
  };
}

function updateNodeInTree(
  tree: AgentNode,
  nodeId: string,
  updater: (node: AgentNode) => AgentNode
): AgentNode {
  if (tree.id === nodeId) return updater(tree);
  return {
    ...tree,
    children: tree.children.map((c) => updateNodeInTree(c, nodeId, updater)),
  };
}

// ─── Export ───────────────────────────────────────────────────────────────────

export function OrchestrationTree() {
  const [tree, setTree] = useState<AgentNode>(DEFAULT_TREE);
  const [selectedId, setSelectedId] = useState<string | null>("root");
  const [knowledgeBases] = useState<KnowledgeBase[]>(DEFAULT_KNOWLEDGE_BASES);
  const [mcpServers] = useState<MCPServerConfig[]>(DEFAULT_MCP_SERVERS);

  const selectedAgent = selectedId ? findNode(tree, selectedId) : null;

  const handleAddChild = useCallback(
    (parentId: string) => {
      const newAgent: AgentNode = {
        id: `agent-${Date.now()}`,
        name: "New Agent",
        model: "GPT-4o-mini",
        role: "worker",
        icon: "worker",
        status: "idle",
        children: [],
        knowledgeBases: [],
        mcpServers: [],
        tools: [],
      };
      setTree((prev) => addChildToNode(prev, parentId, newAgent));
      setSelectedId(newAgent.id);
    },
    []
  );

  const handleRemove = useCallback((nodeId: string) => {
    setTree((prev) => removeNodeFromTree(prev, nodeId));
    setSelectedId(null);
  }, []);

  const handleAttachKB = useCallback((agentId: string, kbId: string) => {
    setTree((prev) =>
      updateNodeInTree(prev, agentId, (node) => ({
        ...node,
        knowledgeBases: [...(node.knowledgeBases || []), kbId],
      }))
    );
  }, []);

  const handleDetachKB = useCallback((agentId: string, kbId: string) => {
    setTree((prev) =>
      updateNodeInTree(prev, agentId, (node) => ({
        ...node,
        knowledgeBases: (node.knowledgeBases || []).filter((id) => id !== kbId),
      }))
    );
  }, []);

  const handleAttachMCP = useCallback((agentId: string, serverId: string) => {
    setTree((prev) =>
      updateNodeInTree(prev, agentId, (node) => ({
        ...node,
        mcpServers: [...(node.mcpServers || []), serverId],
      }))
    );
  }, []);

  const handleDetachMCP = useCallback((agentId: string, serverId: string) => {
    setTree((prev) =>
      updateNodeInTree(prev, agentId, (node) => ({
        ...node,
        mcpServers: (node.mcpServers || []).filter((id) => id !== serverId),
      }))
    );
  }, []);

  return (
    <div className="flex gap-6 h-full min-h-[600px]">
      {/* Left: Tree Visualization */}
      <div className="flex-1 min-w-0">
        <div className="rounded-xl border border-border bg-card/50 p-6 min-h-[600px]">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-accent" />
              </div>
              <div>
                <h3 className="text-sm font-semibold">Agent Hierarchy</h3>
                <p className="text-xs text-muted-foreground">
                  Click to select, drag to reorganize
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => handleAddChild("root")}
            >
              <Plus className="w-3.5 h-3.5" />
              Add Agent
            </Button>
          </div>

          {/* Tree */}
          <div className="space-y-3">
            <TreeNode
              node={tree}
              level={0}
              isLast={true}
              onSelect={setSelectedId}
              selectedId={selectedId}
              onAddChild={handleAddChild}
              onRemove={handleRemove}
            />
          </div>
        </div>
      </div>

      {/* Right: Config Panel */}
      <div className="w-80 shrink-0 space-y-4 overflow-y-auto">
        {/* Agent Details */}
        {selectedAgent && (
          <div className="rounded-xl border border-border bg-card p-4">
            <AgentDetailPanel agent={selectedAgent} />
          </div>
        )}

        {/* Knowledge Bases */}
        <div className="rounded-xl border border-border bg-card p-4">
          <KnowledgeBasePanel
            knowledgeBases={knowledgeBases}
            selectedAgent={selectedAgent}
            onAttach={handleAttachKB}
            onDetach={handleDetachKB}
          />
        </div>

        {/* MCP Servers */}
        <div className="rounded-xl border border-border bg-card p-4">
          <MCPServerPanel
            mcpServers={mcpServers}
            selectedAgent={selectedAgent}
            onAttach={handleAttachMCP}
            onDetach={handleDetachMCP}
          />
        </div>
      </div>
    </div>
  );
}
