"use client";

import {
  BookOpen,
  Award,
  Play,
  MoreHorizontal,
  CheckCircle,
  Clock,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AppLayout } from "@/components/app-layout";
import { courses } from "@/lib/mock-data";

export default function LearningPage() {
  return (
    <AppLayout>
      <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Learning Platform</h1>
        <p className="text-muted-foreground">
          Master AI and AgentThat with our comprehensive courses
        </p>
      </div>

      {/* Learning Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Courses Completed
                </p>
                <p className="text-3xl font-bold">1</p>
                <p className="text-xs text-accent mt-2">25% progress overall</p>
              </div>
              <CheckCircle className="w-5 h-5 text-accent opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Certifications
                </p>
                <p className="text-3xl font-bold">0</p>
                <p className="text-xs text-accent mt-2">Complete courses to earn</p>
              </div>
              <Award className="w-5 h-5 text-accent opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Learning Streak
                </p>
                <p className="text-3xl font-bold">3</p>
                <p className="text-xs text-accent mt-2">Days in a row</p>
              </div>
              <Target className="w-5 h-5 text-accent opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommended Learning Path */}
      <Card>
        <CardHeader>
          <CardTitle>Recommended Learning Path</CardTitle>
          <CardDescription>
            Complete these courses to become an AgentThat expert
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                step: 1,
                title: "AI Fundamentals",
                status: "completed",
              },
              {
                step: 2,
                title: "Prompt Engineering Mastery",
                status: "in_progress",
              },
              {
                step: 3,
                title: "Building Multi-Agent Systems",
                status: "available",
              },
              {
                step: 4,
                title: "Advanced Optimization",
                status: "available",
              },
            ].map((path) => (
              <div
                key={path.step}
                className="flex items-center gap-4 p-4 rounded-lg border border-border"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/20 border border-accent">
                  <span className="text-sm font-semibold text-accent">
                    {path.step}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-medium">{path.title}</p>
                </div>
                {path.status === "completed" && (
                  <Badge variant="success">Completed</Badge>
                )}
                {path.status === "in_progress" && (
                  <Badge variant="info">In Progress</Badge>
                )}
                {path.status === "available" && (
                  <Badge variant="outline">Available</Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Courses */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">All Courses</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {courses.map((course) => (
            <Card
              key={course.id}
              className="hover:border-accent/50 transition-colors flex flex-col"
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{course.title}</CardTitle>
                    <CardDescription className="mt-2">
                      {course.description}
                    </CardDescription>
                  </div>
                  {course.status === "completed" && (
                    <CheckCircle className="w-5 h-5 text-accent flex-shrink-0" />
                  )}
                </div>
              </CardHeader>

              <CardContent className="flex-1 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    {course.duration}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <BookOpen className="w-4 h-4" />
                    {course.lessons} lessons
                  </div>
                </div>

                {course.completion > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-medium">Progress</p>
                      <p className="text-xs text-muted-foreground">
                        {course.completion}%
                      </p>
                    </div>
                    <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent"
                        style={{ width: `${course.completion}%` }}
                      />
                    </div>
                  </div>
                )}

                <Button className="w-full mt-4 gap-2" variant={course.completion > 0 ? "secondary" : "default"}>
                  {course.completion === 0 && (
                    <>
                      <Play className="w-4 h-4" />
                      Start Course
                    </>
                  )}
                  {course.completion > 0 && course.completion < 100 && (
                    <>
                      <Play className="w-4 h-4" />
                      Continue
                    </>
                  )}
                  {course.completion === 100 && (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Completed
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Certifications */}
      <Card>
        <CardHeader>
          <CardTitle>Available Certifications</CardTitle>
          <CardDescription>
            Earn recognized certifications by completing course paths
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                name: "AgentThat Fundamentals",
                courses: 2,
                level: "Beginner",
              },
              {
                name: "Advanced Agent Builder",
                courses: 3,
                level: "Intermediate",
              },
              {
                name: "Enterprise Architect",
                courses: 4,
                level: "Advanced",
              },
              {
                name: "Certified Prompt Engineer",
                courses: 2,
                level: "Advanced",
              },
            ].map((cert, idx) => (
              <Card key={idx} className="border border-accent/20">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold">{cert.name}</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {cert.courses} courses
                      </p>
                    </div>
                    <Award className="w-5 h-5 text-accent opacity-50" />
                  </div>
                  <Badge variant="outline">{cert.level}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
      </div>
    </AppLayout>
  );
}
