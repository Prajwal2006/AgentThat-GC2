"use client";

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Download,
  TrendingUp,
  Users,
  Zap,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppLayout } from "@/components/app-layout";
import { analyticsData } from "@/lib/mock-data";

export default function AnalyticsPage() {
  const roiMetrics = [
    {
      title: "Time Saved (Hours)",
      value: "2,847",
      change: "+12% this month",
      icon: Zap,
    },
    {
      title: "Cost Reduction",
      value: "$450K",
      change: "+18% savings",
      icon: DollarSign,
    },
    {
      title: "User Adoption",
      value: "95%",
      change: "+8% from last quarter",
      icon: Users,
    },
    {
      title: "Efficiency Gain",
      value: "94%",
      change: "+6% improvement",
      icon: TrendingUp,
    },
  ];

  return (
    <AppLayout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">AI Adoption Analytics</h1>
          <p className="text-muted-foreground">
            Track ROI and platform usage across your organization
          </p>
        </div>
        <Button className="gap-2" variant="outline">
          <Download className="w-4 h-4" />
          Export Report
        </Button>
      </div>

      {/* ROI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {roiMetrics.map((metric, idx) => {
          const Icon = metric.icon;
          return (
            <Card key={idx} className="hover:border-accent/50 transition-colors">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      {metric.title}
                    </p>
                    <p className="text-3xl font-bold">{metric.value}</p>
                    <p className="text-xs text-accent mt-2">{metric.change}</p>
                  </div>
                  <Icon className="w-5 h-5 text-accent opacity-50" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Adoption Chart */}
        <Card>
          <CardHeader>
            <CardTitle>User Adoption Rate</CardTitle>
            <CardDescription>
              Percentage of employees using AgentThat
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a2744",
                    border: "1px solid #1e293b",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="adoption"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: "#6366f1", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Efficiency Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Platform Efficiency Score</CardTitle>
            <CardDescription>Overall system performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a2744",
                    border: "1px solid #1e293b",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="efficiency"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  dot={{ fill: "#06b6d4", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Cost Savings Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Savings Impact</CardTitle>
          <CardDescription>Monthly cost reduction in USD</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a2744",
                  border: "1px solid #1e293b",
                }}
              />
              <Legend />
              <Bar
                dataKey="savings"
                fill="#6366f1"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Department Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Adoption by Department</CardTitle>
          <CardDescription>
            Which teams are leading AI adoption
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { dept: "Engineering", adoption: 98, users: 42 },
              { dept: "Sales", adoption: 85, users: 35 },
              { dept: "Marketing", adoption: 92, users: 28 },
              { dept: "Operations", adoption: 78, users: 22 },
              { dept: "HR", adoption: 65, users: 15 },
            ].map((dept, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div className="flex-1">
                  <p className="font-medium text-sm mb-2">{dept.dept}</p>
                  <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-accent"
                      style={{ width: `${dept.adoption}%` }}
                    />
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-sm">{dept.adoption}%</p>
                  <p className="text-xs text-muted-foreground">
                    {dept.users} users
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      </div>
    </AppLayout>
  );
}
