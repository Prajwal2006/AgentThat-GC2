"use client";

import { AppLayout } from "@/components/app-layout";
import { OrchestrationTree } from "@/components/orchestration-tree";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Save, RotateCcw, Download } from "lucide-react";

export default function OrchestrationPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold">Agent Orchestration</h1>
            <p className="text-muted-foreground text-sm">
              Design and visualize your multi-agent hierarchy with knowledge
              bases and MCP servers
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="success">Live</Badge>
            <Button variant="ghost" size="sm" className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Reset
            </Button>
            <Button variant="ghost" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button variant="secondary" size="sm" className="gap-2">
              <Save className="w-4 h-4" />
              Save
            </Button>
            <Button size="sm" className="gap-2">
              <Play className="w-4 h-4" />
              Deploy
            </Button>
          </div>
        </div>

        {/* Tree Visualization */}
        <OrchestrationTree />
      </div>
    </AppLayout>
  );
}
