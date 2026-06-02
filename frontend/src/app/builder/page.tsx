"use client";

import { useState } from "react";
import {
  Plus,
  Wand2,
  Code,
  Sparkles,
  ArrowRight,
  Zap,
  MessageSquare,
  Database,
  Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function AgentBuilder() {
  const [mode, setMode] = useState<"select" | "manual" | "ai">("select");
  const [agentName, setAgentName] = useState("");

  if (mode === "select") {
    return (
      <div className="p-6 lg:p-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Agent Builder</h1>
          <p className="text-muted-foreground">
            Choose how you want to create your AI agent
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Manual Mode */}
          <Card
            className="cursor-pointer hover:border-accent/50 transition-all hover:shadow-lg"
            onClick={() => setMode("manual")}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Code className="w-5 h-5 text-accent" />
                    Manual Builder
                  </CardTitle>
                  <CardDescription className="mt-2">
                    Drag-and-drop visual builder
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-6">
                Build agents step-by-step with our intuitive visual interface.
                Perfect for detailed customization.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <MessageSquare className="w-4 h-4" />
                  Configure prompts & instructions
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Database className="w-4 h-4" />
                  Add tools & integrations
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Settings2 className="w-4 h-4" />
                  Fine-tune parameters
                </div>
              </div>
              <Button className="w-full mt-6 justify-between" variant="default">
                Create Manually
                <ArrowRight className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>

          {/* AI Generation Mode */}
          <Card
            className="cursor-pointer hover:border-accent/50 transition-all hover:shadow-lg border-accent/20 relative"
            onClick={() => setMode("ai")}
          >
            <div className="absolute top-0 right-0 px-3 py-1 bg-accent/10 border border-accent rounded-bl-lg rounded-tr-lg">
              <Badge variant="info" className="text-xs">
                <Sparkles className="w-3 h-3 mr-1" />
                Recommended
              </Badge>
            </div>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Wand2 className="w-5 h-5 text-accent" />
                    AI Generation
                  </CardTitle>
                  <CardDescription className="mt-2">
                    Describe what you need
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-6">
                Just describe your agent in natural language. Our AI architect
                designs and deploys it automatically.
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Zap className="w-4 h-4" />
                  AI-optimized architecture
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Sparkles className="w-4 h-4" />
                  Instant configuration
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <ArrowRight className="w-4 h-4" />
                  Ready to deploy
                </div>
              </div>
              <Button className="w-full mt-6 justify-between" variant="default">
                Generate with AI
                <ArrowRight className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (mode === "ai") {
    return (
      <div className="p-6 lg:p-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Create Agent with AI</h1>
          <p className="text-muted-foreground">
            Describe your agent in natural language
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Describe Your Agent</CardTitle>
            <CardDescription>
              The more details you provide, the better the AI architect can design your agent
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">Agent Name</label>
              <Input
                placeholder="e.g., Customer Support Agent"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                What should this agent do?
              </label>
              <textarea
                className="w-full h-32 rounded-lg border border-border bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Example: Create a customer support agent that classifies tickets, searches our knowledge base, drafts responses, escalates urgent issues to humans, and updates our ticketing system."
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                What tools and integrations does it need?
              </label>
              <textarea
                className="w-full h-24 rounded-lg border border-border bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Example: Slack integration, Jira API, Knowledge base search, Email notifications"
              />
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setMode("select");
                  setAgentName("");
                }}
              >
                Cancel
              </Button>
              <Button className="flex-1 gap-2">
                <Wand2 className="w-4 h-4" />
                Generate Agent Architecture
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Preview Card */}
        {agentName && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Generation Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                  <div className="text-xs text-muted-foreground mb-1">
                    Agents
                  </div>
                  <div className="text-2xl font-bold">3</div>
                </div>
                <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                  <div className="text-xs text-muted-foreground mb-1">
                    Integrations
                  </div>
                  <div className="text-2xl font-bold">2</div>
                </div>
                <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                  <div className="text-xs text-muted-foreground mb-1">
                    Tools
                  </div>
                  <div className="text-2xl font-bold">5</div>
                </div>
                <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                  <div className="text-xs text-muted-foreground mb-1">
                    Est. Cost
                  </div>
                  <div className="text-2xl font-bold">Low</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Create Agent Manually</h1>
        <p className="text-muted-foreground">
          Use the visual builder to create your agent step-by-step
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Agent Configuration</CardTitle>
          <CardDescription>
            Create a new AI agent with custom prompts, tools, and integrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-sm font-medium mb-2 block">Agent Name</label>
            <Input
              placeholder="e.g., Customer Support Agent"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              System Prompt
            </label>
            <textarea
              className="w-full h-32 rounded-lg border border-border bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="Define how your agent should behave, respond, and make decisions..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Model</label>
              <select className="w-full rounded-lg border border-border bg-secondary px-4 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-accent">
                <option>GPT-4 Turbo</option>
                <option>GPT-4</option>
                <option>Claude 3 Opus</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                Temperature
              </label>
              <Input
                type="number"
                min="0"
                max="1"
                step="0.1"
                defaultValue="0.7"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-3 block">Tools</label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {["Web Search", "File Upload", "API Call", "Database Query", "Email", "Slack"].map(
                (tool) => (
                  <Button
                    key={tool}
                    variant="outline"
                    className="justify-start"
                    onClick={(e) => {
                      e.currentTarget.classList.toggle("border-accent");
                    }}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    {tool}
                  </Button>
                )
              )}
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setMode("select");
                setAgentName("");
              }}
            >
              Cancel
            </Button>
            <Button className="flex-1">Create Agent</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
