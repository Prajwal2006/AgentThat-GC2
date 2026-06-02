"use client";

import { useState } from "react";
import {
  Plus,
  Play,
  Pause,
  MoreHorizontal,
  Clock,
  Users,
  Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { AppLayout } from "@/components/app-layout";
import { workflows } from "@/lib/mock-data";
import { WorkflowItem, apiPost, useApiResource } from "@/lib/api";

export default function WorkflowsPage() {
  const { data, loading, error, setData } = useApiResource<WorkflowItem[]>("/v1/workflows", workflows);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [newWorkflowDescription, setNewWorkflowDescription] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const createWorkflow = async () => {
    try {
      const created = await apiPost<WorkflowItem>("/v1/workflows", {
        name: newWorkflowName,
        description: newWorkflowDescription,
        agents: 2,
      });
      setData((current) => [created, ...current]);
      setStatusMessage(`Created workflow: ${created.name}`);
      setNewWorkflowName("");
      setNewWorkflowDescription("");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not create workflow.");
    }
  };

  const controlWorkflow = async (workflow: WorkflowItem, action: "run" | "pause" | "resume") => {
    try {
      const updated = await apiPost<WorkflowItem>(`/v1/workflows/${workflow.id}/control`, { action });
      setData((current) =>
        current.map((item) => (item.id === updated.id ? updated : item))
      );
      setStatusMessage(`${updated.name} is now ${updated.status}.`);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not update workflow.");
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Workflow Studio</h1>
          <p className="text-muted-foreground">
            Design and orchestrate multi-agent workflows
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={error ? "destructive" : loading ? "info" : "success"}>
            {error ? "Backend offline" : loading ? "Syncing" : "Live workflows"}
          </Badge>
          <Button className="gap-2" onClick={createWorkflow} disabled={newWorkflowName.trim().length < 3 || newWorkflowDescription.trim().length < 8}>
            <Plus className="w-4 h-4" />
            New Workflow
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-3">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <Input
              placeholder="Workflow name"
              value={newWorkflowName}
              onChange={(event) => setNewWorkflowName(event.target.value)}
            />
            <Input
              placeholder="Workflow description"
              value={newWorkflowDescription}
              onChange={(event) => setNewWorkflowDescription(event.target.value)}
            />
          </div>
          {statusMessage && <Badge variant="info">{statusMessage}</Badge>}
        </CardContent>
      </Card>

      {/* Workflow List */}
      <div className="space-y-4">
        {data.map((workflow) => (
          <Card
            key={workflow.id}
            className="hover:border-accent/50 transition-colors cursor-pointer"
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Workflow className="w-5 h-5 text-accent" />
                    <h3 className="text-lg font-semibold">{workflow.name}</h3>
                    <Badge
                      variant={
                        workflow.status === "active"
                          ? "default"
                          : "info"
                      }
                    >
                      {workflow.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">
                    {workflow.description}
                  </p>

                  <div className="flex flex-wrap items-center gap-6 text-xs">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Users className="w-4 h-4" />
                      {workflow.agents} agents
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="w-4 h-4" />
                      Last run: {workflow.lastRun}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      controlWorkflow(
                        workflow,
                        workflow.status === "active"
                          ? "pause"
                          : workflow.status === "paused"
                          ? "resume"
                          : "run"
                      )
                    }
                  >
                    {workflow.status === "active" ? (
                      <Pause className="w-5 h-5" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                  </Button>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Templates Section */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Workflow Templates</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              name: "Sales Pipeline Automation",
              agents: 3,
              tools: 5,
            },
            {
              name: "Customer Support Multi-Agent",
              agents: 2,
              tools: 4,
            },
            {
              name: "Content Production Workflow",
              agents: 4,
              tools: 6,
            },
          ].map((template, idx) => (
            <Card key={idx} className="hover:border-accent/50 transition-colors cursor-pointer">
              <CardHeader>
                <CardTitle className="text-lg">{template.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
                    <div className="text-xs text-muted-foreground mb-1">
                      Agents
                    </div>
                    <div className="text-xl font-bold">{template.agents}</div>
                  </div>
                  <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
                    <div className="text-xs text-muted-foreground mb-1">
                      Tools
                    </div>
                    <div className="text-xl font-bold">{template.tools}</div>
                  </div>
                </div>
                <Button className="w-full" variant="outline">
                  Use Template
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      </div>
    </AppLayout>
  );
}
