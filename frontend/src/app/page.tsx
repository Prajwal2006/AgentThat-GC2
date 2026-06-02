"use client";

import { useRouter } from "next/navigation";
import {
  Zap,
  Workflow,
  Users,
  TrendingUp,
  Play,
  Plus,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { dashboardStats, recentActivity, agents } from "@/lib/mock-data";
import { PlatformOverview, useApiResource } from "@/lib/api";

const icons: Record<string, React.ReactNode> = {
  Zap: <Zap className="w-5 h-5" />,
  Workflow: <Workflow className="w-5 h-5" />,
  Users: <Users className="w-5 h-5" />,
  TrendingUp: <TrendingUp className="w-5 h-5" />,
};

export default function Dashboard() {
  const router = useRouter();
  const { data, loading, error } = useApiResource<PlatformOverview>(
    "/v1/platform/overview",
    { dashboardStats, recentActivity, agents }
  );

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      
      <main className="flex-1 lg:ml-64">
        <Header />
        
        <div className="p-6 lg:p-8 space-y-8">
          {/* Welcome Section */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-4xl font-bold">Welcome back, Sarah</h1>
                <p className="text-muted-foreground">
                  Here&apos;s what&apos;s happening with your AI platform
                </p>
              </div>
              <Badge variant={error ? "destructive" : loading ? "info" : "success"}>
                {error ? "Backend offline" : loading ? "Syncing" : "Backend connected"}
              </Badge>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {data.dashboardStats.map((stat, idx) => (
              <Card key={idx} className="hover:border-accent/50 transition-colors">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">
                        {stat.title}
                      </p>
                      <p className="text-3xl font-bold">{stat.value}</p>
                      <p className="text-xs text-accent mt-2">{stat.change}</p>
                    </div>
                    <div className="text-accent opacity-50">
                      {icons[stat.icon]}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Actions and Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start gap-2" variant="secondary" onClick={() => router.push("/builder")}>
                  <Plus className="w-4 h-4" />
                  New Agent
                </Button>
                <Button className="w-full justify-start gap-2" variant="secondary" onClick={() => router.push("/workflows")}>
                  <Workflow className="w-4 h-4" />
                  New Workflow
                </Button>
                <Button className="w-full justify-start gap-2" variant="secondary" onClick={() => router.push("/marketplace")}>
                  <Play className="w-4 h-4" />
                  Browse Templates
                </Button>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-lg">Recent Activity</CardTitle>
                <CardDescription>Your team&apos;s latest actions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.recentActivity.map((activity) => (
                    <div
                      key={activity.id}
                      className="flex items-start justify-between border-b border-border pb-4 last:border-0"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-sm">{activity.title}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {activity.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            activity.status === "success"
                              ? "success"
                              : activity.status === "active"
                              ? "default"
                              : "info"
                          }
                        >
                          {activity.status}
                        </Badge>
                        <p className="text-xs text-muted-foreground whitespace-nowrap">
                          {activity.timestamp}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Agents */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Active Agents</CardTitle>
                  <CardDescription>All your deployed agents</CardDescription>
                </div>
                <Button variant="outline">View All</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.agents.slice(0, 3).map((agent) => (
                  <div
                    key={agent.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-white/5 transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {agent.description}
                      </p>
                      <div className="flex items-center gap-4 mt-2">
                        <Badge variant="outline">{agent.category}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {agent.usage} uses
                        </span>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <ArrowUpRight className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
