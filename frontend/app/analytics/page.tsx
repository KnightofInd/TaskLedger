"use client";

import { Header } from "@/components/shared/Header";
import { Icon } from "@/components/shared/Icon";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Mock analytics data
const overviewStats = [
  { label: "Total Meetings", value: "128", change: "+12%", trend: "up", icon: "meeting_room" },
  { label: "Action Items", value: "342", change: "+18%", trend: "up", icon: "task_alt" },
  { label: "Completion Rate", value: "73%", change: "+5%", trend: "up", icon: "trending_up" },
  { label: "Avg Confidence", value: "85%", change: "+3%", trend: "up", icon: "psychology" },
];

const teamPerformance = [
  { name: "Sarah Chen", completed: 45, pending: 8, completionRate: 85, confidence: 92 },
  { name: "Michael Torres", completed: 38, pending: 12, completionRate: 76, confidence: 88 },
  { name: "Emma Davis", completed: 52, pending: 5, completionRate: 91, confidence: 90 },
  { name: "Alex Kim", completed: 29, pending: 15, completionRate: 66, confidence: 78 },
  { name: "Maya Patel", completed: 41, pending: 7, completionRate: 85, confidence: 86 },
];

const weeklyTrends = [
  { week: "Week 1", meetings: 12, actions: 45, completed: 32 },
  { week: "Week 2", meetings: 15, actions: 58, completed: 41 },
  { week: "Week 3", meetings: 18, actions: 62, completed: 48 },
  { week: "Week 4", meetings: 14, actions: 51, completed: 38 },
];

const priorityDistribution = [
  { priority: "HIGH", count: 45, color: "bg-red-600", percentage: 32 },
  { priority: "MEDIUM", count: 68, color: "bg-amber-600", percentage: 48 },
  { priority: "LOW", count: 28, color: "bg-slate-400", percentage: 20 },
];

const confidenceDistribution = [
  { level: "HIGH (80-100%)", count: 112, color: "bg-green-600", percentage: 65 },
  { level: "MEDIUM (60-79%)", count: 48, color: "bg-yellow-600", percentage: 28 },
  { level: "LOW (0-59%)", count: 12, color: "bg-red-600", percentage: 7 },
];

const meetingInsights = [
  { type: "Most Productive Day", value: "Wednesday", icon: "calendar_today", color: "text-primary" },
  { type: "Avg Meeting Duration", value: "45 mins", icon: "schedule", color: "text-slate-600" },
  { type: "Total Participants", value: "24", icon: "people", color: "text-slate-600" },
  { type: "Risk Flags Raised", value: "156", icon: "warning", color: "text-red-600" },
];

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      
      <main className="flex-1 py-8 px-6">
        <div className="max-w-[1400px] mx-auto space-y-8">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-black tracking-tight mb-2">Analytics Dashboard</h1>
              <p className="text-muted-foreground text-xl">
                Insights and trends from your meeting action items
              </p>
            </div>
            <Select defaultValue="30days">
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7days">Last 7 Days</SelectItem>
                <SelectItem value="30days">Last 30 Days</SelectItem>
                <SelectItem value="90days">Last 90 Days</SelectItem>
                <SelectItem value="year">This Year</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {overviewStats.map((stat) => (
              <Card key={stat.label} className="shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="size-12 rounded-xl bg-primary/10 flex items-center justify-center">
                      <Icon name={stat.icon} className="text-2xl text-primary" />
                    </div>
                    <Badge 
                      variant="secondary" 
                      className="bg-green-100 text-green-700 hover:bg-green-100"
                    >
                      {stat.change}
                    </Badge>
                  </div>
                  <p className="text-base font-medium text-muted-foreground mb-1">{stat.label}</p>
                  <p className="text-3xl font-black">{stat.value}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Weekly Trends Chart */}
            <Card className="lg:col-span-2 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold">Weekly Activity Trends</h2>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="size-3 rounded-full bg-primary"></div>
                      <span className="text-muted-foreground">Meetings</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="size-3 rounded-full bg-amber-600"></div>
                      <span className="text-muted-foreground">Actions Created</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="size-3 rounded-full bg-green-600"></div>
                      <span className="text-muted-foreground">Completed</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-6">
                  {weeklyTrends.map((week) => {
                    const maxValue = Math.max(...weeklyTrends.map(w => w.actions));
                    return (
                      <div key={week.week} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium text-slate-900 dark:text-white w-20">{week.week}</span>
                          <div className="flex-1 mx-4 grid grid-cols-3 gap-2">
                            {/* Meetings */}
                            <div className="relative h-8 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
                              <div 
                                className="absolute inset-y-0 left-0 bg-primary rounded flex items-center justify-center text-white text-xs font-bold"
                                style={{ width: `${(week.meetings / maxValue) * 100}%` }}
                              >
                                {week.meetings}
                              </div>
                            </div>
                            {/* Actions */}
                            <div className="relative h-8 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
                              <div 
                                className="absolute inset-y-0 left-0 bg-amber-600 rounded flex items-center justify-center text-white text-xs font-bold"
                                style={{ width: `${(week.actions / maxValue) * 100}%` }}
                              >
                                {week.actions}
                              </div>
                            </div>
                            {/* Completed */}
                            <div className="relative h-8 bg-slate-100 dark:bg-slate-800 rounded overflow-hidden">
                              <div 
                                className="absolute inset-y-0 left-0 bg-green-600 rounded flex items-center justify-center text-white text-xs font-bold"
                                style={{ width: `${(week.completed / maxValue) * 100}%` }}
                              >
                                {week.completed}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Meeting Insights */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-6">Meeting Insights</h2>
                <div className="space-y-4">
                  {meetingInsights.map((insight) => (
                    <div key={insight.type} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Icon name={insight.icon} className={`text-xl ${insight.color}`} />
                        <div>
                          <p className="text-xs text-muted-foreground">{insight.type}</p>
                          <p className="text-lg font-bold">{insight.value}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Priority Distribution */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-6">Priority Distribution</h2>
                <div className="space-y-4">
                  {priorityDistribution.map((item) => (
                    <div key={item.priority} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <Badge className={`${
                            item.priority === "HIGH" ? "bg-red-100 text-red-700" :
                            item.priority === "MEDIUM" ? "bg-amber-100 text-amber-700" :
                            "bg-slate-200 text-slate-700"
                          }`}>
                            {item.priority}
                          </Badge>
                          <span className="font-medium">{item.count} items</span>
                        </div>
                        <span className="font-bold">{item.percentage}%</span>
                      </div>
                      <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${item.color} rounded-full transition-all`}
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Confidence Distribution */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <h2 className="text-xl font-bold mb-6">Confidence Score Distribution</h2>
                <div className="space-y-4">
                  {confidenceDistribution.map((item) => (
                    <div key={item.level} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{item.level}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">{item.count} items</span>
                          <span className="font-bold">{item.percentage}%</span>
                        </div>
                      </div>
                      <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${item.color} rounded-full transition-all`}
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Team Performance */}
          <Card className="shadow-sm">
            <CardContent className="p-6">
              <h2 className="text-xl font-bold mb-6">Team Performance</h2>
              <div className="space-y-4">
                {teamPerformance.map((member) => (
                  <div key={member.name} className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                          {member.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                          <p className="font-bold">{member.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {member.completed} completed • {member.pending} pending
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground mb-1">Completion Rate</p>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${
                                  member.completionRate >= 85 ? "bg-green-600" :
                                  member.completionRate >= 70 ? "bg-yellow-600" :
                                  "bg-red-600"
                                }`}
                                style={{ width: `${member.completionRate}%` }}
                              />
                            </div>
                            <span className="text-sm font-bold">{member.completionRate}%</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground mb-1">Avg Confidence</p>
                          <Badge className={`${
                            member.confidence >= 85 ? "bg-green-100 text-green-700" :
                            member.confidence >= 70 ? "bg-yellow-100 text-yellow-700" :
                            "bg-red-100 text-red-700"
                          }`}>
                            {member.confidence}%
                          </Badge>
                        </div>
                      </div>
                    </div>
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
