"use client";

import { useState } from "react";
import {
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
import { AppLayout } from "@/components/app-layout";
import {
  Agent,
  DeploySolutionResponse,
  GeneratedSolution,
  ImprovePromptResponse,
  apiPost,
} from "@/lib/api";

export default function AgentBuilder() {
  const [mode, setMode] = useState<"select" | "manual" | "ai">("select");
  const [agentName, setAgentName] = useState("");
  const [description, setDescription] = useState("");
  const [businessContext, setBusinessContext] = useState("");
  const [improvedPrompt, setImprovedPrompt] = useState<ImprovePromptResponse | null>(null);
  const [solution, setSolution] = useState<GeneratedSolution | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const resetBuilder = () => {
    setMode("select");
    setAgentName("");
    setDescription("");
    setBusinessContext("");
    setImprovedPrompt(null);
    setSolution(null);
    setStatusMessage(null);
  };

  const saveManualAgent = async () => {
    setIsSaving(true);
    setStatusMessage(null);
    try {
      const saved = await apiPost<Agent>("/v1/agents", {
        name: agentName,
        description,
        category: "General",
      });
      setStatusMessage(`${saved.name} saved as a testing agent.`);
      setAgentName("");
      setDescription("");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Could not save agent.");
    } finally {
      setIsSaving(false);
    }
  };

  const improvePrompt = async () => {
    setIsImproving(true);
    setStatusMessage(null);
    try {
      const result = await apiPost<ImprovePromptResponse>("/v1/ai/improve-prompt", {
        prompt: description,
        business_context: businessContext,
      });
      setImprovedPrompt(result);
      setDescription(result.improved_prompt);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Could not improve prompt.");
    } finally {
      setIsImproving(false);
    }
  };

  const generateSolution = async () => {
    setIsGenerating(true);
    setStatusMessage(null);
    setSolution(null);
    try {
      const result = await apiPost<GeneratedSolution>("/v1/solutions/generate", {
        name: agentName || "Generated AgentThat Workflow",
        requirement: description,
        mode: "workflow",
        department: businessContext,
      });
      setSolution(result);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Could not generate architecture.");
    } finally {
      setIsGenerating(false);
    }
  };

  const deploySolution = async () => {
    if (!solution) {
      return;
    }
    setIsDeploying(true);
    setStatusMessage(null);
    try {
      const result = await apiPost<DeploySolutionResponse>("/v1/solutions/deploy", {
        solution,
      });
      setStatusMessage(
        `Deployed workflow ${result.workflowId} with ${result.agentsCreated} agents.`
      );
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Could not deploy solution.");
    } finally {
      setIsDeploying(false);
    }
  };

  if (mode === "select") {
    return (
      <AppLayout>
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Agent Builder</h1>
          <p className="text-muted-foreground">
            Choose how you want to create your AI agent
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
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
                  <Zap className="w-4 h-4" />
                  Deploy in seconds
                </div>
              </div>
              <Button className="w-full mt-6 justify-between">
                Use AI Generation
                <ArrowRight className="w-4 h-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  if (mode === "manual") {
    return (
      <AppLayout>
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Manual Agent Builder</h1>
          <p className="text-muted-foreground">
            Build your agent step-by-step
          </p>
        </div>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Agent Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">Agent Name</label>
              <Input
                placeholder="Enter agent name"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Description</label>
              <textarea
                className="w-full h-24 rounded-lg border border-border bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="Describe what this agent does..."
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </div>

            {statusMessage && (
              <Badge variant={statusMessage.includes("saved") ? "success" : "info"}>
                {statusMessage}
              </Badge>
            )}

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={resetBuilder}
              >
                Back
              </Button>
              <Button
                className="flex-1"
                onClick={saveManualAgent}
                disabled={isSaving || agentName.trim().length < 2 || description.trim().length < 4}
              >
                {isSaving ? "Saving..." : "Save Agent"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </AppLayout>
    );
  }

  // AI Mode
  return (
    <AppLayout>
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Create Agent with AI</h1>
        <p className="text-muted-foreground">
          Describe your agent in natural language
        </p>
      </div>

      <Card className="mt-8">
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
              placeholder="Example: Create a customer support agent that classifies tickets, searches our knowledge base, drafts responses, escalates urgent issues to humans..."
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              Department or business context
            </label>
            <Input
              placeholder="e.g., Support, Sales, HR, Operations"
              value={businessContext}
              onChange={(event) => setBusinessContext(event.target.value)}
            />
          </div>

          {statusMessage && <Badge variant="info">{statusMessage}</Badge>}

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={resetBuilder}
            >
              Cancel
            </Button>
            <Button
              variant="secondary"
              className="flex-1 gap-2"
              onClick={improvePrompt}
              disabled={isImproving || description.trim().length < 3}
            >
              <Sparkles className="w-4 h-4" />
              {isImproving ? "Improving..." : "Improve Prompt"}
            </Button>
            <Button
              className="flex-1 gap-2"
              onClick={generateSolution}
              disabled={isGenerating || description.trim().length < 8}
            >
              <Wand2 className="w-4 h-4" />
              {isGenerating ? "Generating..." : "Generate Architecture"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {improvedPrompt && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Prompt Improvement</CardTitle>
            <CardDescription>
              Provider: {improvedPrompt.provider === "azure_openai" ? "Azure OpenAI" : "Fallback engine"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{improvedPrompt.improved_prompt}</p>
            <div className="flex flex-wrap gap-2">
              {improvedPrompt.improvements.map((improvement) => (
                <Badge key={improvement} variant="outline">
                  {improvement}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {solution && (
        <div className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle>{solution.name}</CardTitle>
                  <CardDescription>{solution.summary}</CardDescription>
                </div>
                <Badge variant={solution.provider === "azure_openai" ? "success" : "info"}>
                  {solution.provider === "azure_openai" ? "Azure OpenAI" : "Fallback"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold mb-2">Agents</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {solution.agents.map((agent) => (
                    <div key={agent.name} className="rounded-lg border border-border p-4">
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-muted-foreground mt-1">{agent.purpose}</p>
                      <div className="flex flex-wrap gap-2 mt-3">
                        {agent.tools.map((tool) => (
                          <Badge key={tool} variant="outline">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold mb-2">Workflow</h3>
                <div className="space-y-3">
                  {solution.workflow.map((step) => (
                    <div key={step.id} className="rounded-lg border border-border p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium">{step.name}</p>
                        {step.human_approval && <Badge variant="info">Human approval</Badge>}
                      </div>
                      <p className="text-xs text-accent mt-1">{step.agent}</p>
                      <p className="text-sm text-muted-foreground mt-2">{step.action}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  ["Integrations", solution.integrations],
                  ["Governance", solution.governance],
                  ["Observability", solution.observability],
                ].map(([title, values]) => (
                  <div key={title as string} className="rounded-lg border border-border p-4">
                    <h3 className="text-sm font-semibold mb-3">{title as string}</h3>
                    <div className="space-y-2">
                      {(values as string[]).map((value) => (
                        <p key={value} className="text-sm text-muted-foreground">
                          {value}
                        </p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end">
                <Button onClick={deploySolution} disabled={isDeploying}>
                  {isDeploying ? "Deploying..." : "Deploy Solution"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </AppLayout>
  );
}
