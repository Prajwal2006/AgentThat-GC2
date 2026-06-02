"use client";

import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Bell, Shield, Users, Key } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 lg:ml-0">
        <Header />
        
        <div className="p-6 lg:p-8 space-y-8">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Manage your account and preferences</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Settings Sidebar */}
            <div className="space-y-2">
              <Button variant="ghost" className="w-full justify-start">
                Profile
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                Notifications
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                Security
              </Button>
              <Button variant="ghost" className="w-full justify-start">
                Team
              </Button>
            </div>

            {/* Settings Content */}
            <div className="lg:col-span-3 space-y-6">
              {/* Profile Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Profile Settings
                  </CardTitle>
                  <CardDescription>Manage your personal information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Full Name
                    </label>
                    <Input placeholder="Sarah Chen" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Email Address
                    </label>
                    <Input placeholder="sarah@company.com" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Role
                    </label>
                    <select className="w-full rounded-lg border border-border bg-secondary px-4 py-2 text-foreground">
                      <option>Admin</option>
                      <option>Developer</option>
                      <option>User</option>
                    </select>
                  </div>
                  <Button>Save Changes</Button>
                </CardContent>
              </Card>

              {/* Notification Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Bell className="w-5 h-5" />
                    Notifications
                  </CardTitle>
                  <CardDescription>Control how you receive updates</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { label: "Agent deployments", checked: true },
                    { label: "Workflow runs", checked: true },
                    { label: "Team invitations", checked: true },
                    { label: "Weekly reports", checked: false },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        defaultChecked={item.checked}
                        className="w-4 h-4"
                      />
                      <label className="text-sm">{item.label}</label>
                    </div>
                  ))}
                  <Button className="mt-4">Save Preferences</Button>
                </CardContent>
              </Card>

              {/* API Keys */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="w-5 h-5" />
                    API Keys
                  </CardTitle>
                  <CardDescription>Manage your API access</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                      <div>
                        <p className="text-sm font-medium">Production Key</p>
                        <p className="text-xs text-muted-foreground">
                          sk_live_***
                        </p>
                      </div>
                      <Badge variant="success">Active</Badge>
                    </div>
                  </div>
                  <Button variant="outline">Generate New Key</Button>
                </CardContent>
              </Card>

              {/* Team Management */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Team Members
                  </CardTitle>
                  <CardDescription>Manage your team</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { name: "Sarah Chen", role: "Admin", status: "Active" },
                    { name: "Mike Johnson", role: "Developer", status: "Active" },
                    { name: "James Wilson", role: "User", status: "Active" },
                  ].map((member, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-lg border border-border"
                    >
                      <div>
                        <p className="text-sm font-medium">{member.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {member.role}
                        </p>
                      </div>
                      <Badge variant="outline">{member.status}</Badge>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full">
                    Invite Team Member
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
