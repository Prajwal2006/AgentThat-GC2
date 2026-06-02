"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AppLayout } from "@/components/app-layout";
import { Bell, Shield, Users, Key } from "lucide-react";
import {
  AiStatus,
  NotificationItem,
  ProfileSettings,
  TeamMember,
  apiGet,
  apiPost,
  apiPut,
  useApiResource,
} from "@/lib/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState<ProfileSettings>({
    full_name: "Sarah Chen",
    email: "sarah@company.com",
    role: "Admin",
  });
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    { label: "Agent deployments", enabled: true },
    { label: "Workflow runs", enabled: true },
    { label: "Team invitations", enabled: true },
    { label: "Weekly reports", enabled: false },
  ]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { id: "team-1", name: "Sarah Chen", role: "Admin", status: "Active" },
    { id: "team-2", name: "Mike Johnson", role: "Developer", status: "Active" },
    { id: "team-3", name: "James Wilson", role: "User", status: "Active" },
  ]);
  const [inviteName, setInviteName] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const { data: aiStatus, loading, error } = useApiResource<AiStatus>("/v1/ai/status", {
    provider: "azure_openai",
    configured: false,
    deployment: null,
    apiVersion: "2024-10-21",
    mode: "deterministic-fallback",
  });

  useEffect(() => {
    apiGet<ProfileSettings>("/v1/settings/profile")
      .then(setProfile)
      .catch(() => undefined);
    apiGet<NotificationItem[]>("/v1/settings/notifications")
      .then(setNotifications)
      .catch(() => undefined);
    apiGet<TeamMember[]>("/v1/team/members")
      .then(setTeamMembers)
      .catch(() => undefined);
  }, []);

  const saveProfile = async () => {
    try {
      const saved = await apiPut<ProfileSettings>("/v1/settings/profile", profile);
      setProfile(saved);
      setStatusMessage("Profile updated.");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not save profile.");
    }
  };

  const saveNotifications = async () => {
    try {
      const saved = await apiPut<NotificationItem[]>("/v1/settings/notifications", notifications);
      setNotifications(saved);
      setStatusMessage("Notification preferences updated.");
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not save notifications.");
    }
  };

  const inviteMember = async () => {
    try {
      const member = await apiPost<TeamMember>("/v1/team/members", {
        name: inviteName,
        role: "User",
      });
      setTeamMembers((current) => [...current, member]);
      setInviteName("");
      setStatusMessage(`Invitation sent to ${member.name}.`);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not invite member.");
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Manage your account and preferences</p>
            {statusMessage && <Badge variant="info">{statusMessage}</Badge>}
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
                    <Input
                      placeholder="Sarah Chen"
                      value={profile.full_name}
                      onChange={(event) =>
                        setProfile((current) => ({ ...current, full_name: event.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Email Address
                    </label>
                    <Input
                      placeholder="sarah@company.com"
                      value={profile.email}
                      onChange={(event) =>
                        setProfile((current) => ({ ...current, email: event.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Role
                    </label>
                    <select
                      className="w-full rounded-lg border border-border bg-secondary px-4 py-2 text-foreground"
                      value={profile.role}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          role: event.target.value as ProfileSettings["role"],
                        }))
                      }
                    >
                      <option>Admin</option>
                      <option>Developer</option>
                      <option>User</option>
                    </select>
                  </div>
                  <Button onClick={saveProfile}>Save Changes</Button>
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
                  {notifications.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={item.enabled}
                        onChange={(event) =>
                          setNotifications((current) =>
                            current.map((value, currentIdx) =>
                              currentIdx === idx ? { ...value, enabled: event.target.checked } : value
                            )
                          )
                        }
                        className="w-4 h-4"
                      />
                      <label className="text-sm">{item.label}</label>
                    </div>
                  ))}
                  <Button className="mt-4" onClick={saveNotifications}>Save Preferences</Button>
                </CardContent>
              </Card>

              {/* API Keys */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="w-5 h-5" />
                    AI Services
                  </CardTitle>
                  <CardDescription>Azure OpenAI connection status</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                      <div>
                        <p className="text-sm font-medium">Azure OpenAI</p>
                        <p className="text-xs text-muted-foreground">
                          {aiStatus.deployment
                            ? `Deployment: ${aiStatus.deployment}`
                            : "Add backend Azure values to enable live generation"}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          API version: {aiStatus.apiVersion}
                        </p>
                      </div>
                      <Badge
                        variant={
                          error ? "destructive" : aiStatus.configured ? "success" : loading ? "info" : "outline"
                        }
                      >
                        {error ? "Offline" : aiStatus.configured ? "Live" : loading ? "Checking" : "Fallback"}
                      </Badge>
                    </div>
                  </div>
                  <Button variant="outline">Rotate in Azure Key Vault</Button>
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
                  {teamMembers.map((member) => (
                    <div
                      key={member.id}
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
                  <Input
                    placeholder="New team member name"
                    value={inviteName}
                    onChange={(event) => setInviteName(event.target.value)}
                  />
                  <Button variant="outline" className="w-full" onClick={inviteMember} disabled={inviteName.trim().length < 2}>
                    Invite Team Member
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
      </div>
    </AppLayout>
  );
}
