"use client";

import {
  Plus,
  Play,
  Pause,
  MoreHorizontal,
  Calendar,
  Clock,
  Users,
  Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AppLayout } from "@/components/app-layout";
import { workflows } from "@/lib/mock-data";

export default function WorkflowsPage() {
  return (
    <AppLayout>
      <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Workflow Studio</h1>
          <p className="text-muted-foreground">
            Design and orchestrate multi-agent workflows
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          New Workflow
        </Button>
      </div>

      {/* Workflow List */}
      <div className="space-y-4">
        {workflows.map((workflow) => (
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
                  <Button variant="ghost" size="icon">
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
    </AppLayout>
  );
}
