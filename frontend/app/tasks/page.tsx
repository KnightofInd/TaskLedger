"use client";

import { useState } from "react";
import { Header } from "@/components/shared/Header";
import { Icon } from "@/components/shared/Icon";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

// Placeholder data
const actionItems = [
  {
    id: "1",
    description: "Finalize Q4 product roadmap and share with stakeholders",
    owner: "Sarah Chen",
    deadline: "2024-10-28",
    priority: "HIGH",
    confidence: "HIGH",
    confidenceScore: 92,
    isComplete: false,
    riskFlags: 0,
    meetingTitle: "Q4 Product Roadmap Sync"
  },
  {
    id: "2",
    description: "Prepare technical specifications for new features",
    owner: "Michael Torres",
    deadline: "2024-10-26",
    priority: "MEDIUM",
    confidence: "MEDIUM",
    confidenceScore: 78,
    isComplete: false,
    riskFlags: 2,
    meetingTitle: "Q4 Product Roadmap Sync"
  },
  {
    id: "3",
    description: "Create design mockups for dashboard redesign",
    owner: "Emma Davis",
    deadline: "2024-10-25",
    priority: "HIGH",
    confidence: "HIGH",
    confidenceScore: 88,
    isComplete: true,
    riskFlags: 0,
    meetingTitle: "Engineering Sprint Planning"
  },
  {
    id: "4",
    description: "Review and approve marketing campaign budget",
    owner: null,
    deadline: null,
    priority: "LOW",
    confidence: "LOW",
    confidenceScore: 45,
    isComplete: false,
    riskFlags: 3,
    meetingTitle: "Marketing Campaign Review"
  },
];

export default function TasksPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [confidenceFilter, setConfidenceFilter] = useState("all");

  const getConfidenceBadge = (confidence: string, score: number) => {
    if (confidence === "HIGH") {
      return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">HIGH {score}%</Badge>;
    } else if (confidence === "MEDIUM") {
      return <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">MEDIUM {score}%</Badge>;
    }
    return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">LOW {score}%</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    if (priority === "HIGH") {
      return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">HIGH</Badge>;
    } else if (priority === "MEDIUM") {
      return <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">MEDIUM</Badge>;
    }
    return <Badge variant="secondary">LOW</Badge>;
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Filters */}
        <aside className="w-72 border-r border-border bg-card p-6 flex flex-col gap-8 overflow-y-auto">
          <div className="space-y-6">
            <h1 className="text-xl font-bold">Filters</h1>
            
            {/* Search */}
            <div className="relative">
              <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-[20px]" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                placeholder="Search filters..."
              />
            </div>

            {/* Owner Filter */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Owner</p>
              <Select value={ownerFilter} onValueChange={setOwnerFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Members" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Members</SelectItem>
                  <SelectItem value="sarah">Sarah Chen</SelectItem>
                  <SelectItem value="michael">Michael Torres</SelectItem>
                  <SelectItem value="emma">Emma Davis</SelectItem>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Priority Filter */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Priority</p>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox id="priority-high" />
                  <span className="text-sm">High Priority</span>
                  <Badge className="ml-auto bg-red-100 text-red-700">3</Badge>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox id="priority-medium" />
                  <span className="text-sm">Medium Priority</span>
                  <Badge className="ml-auto bg-amber-100 text-amber-700">5</Badge>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox id="priority-low" />
                  <span className="text-sm">Low Priority</span>
                  <Badge className="ml-auto" variant="secondary">2</Badge>
                </label>
              </div>
            </div>

            {/* Status Filter */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</p>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="complete">Complete</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Confidence Filter */}
            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Confidence</p>
              <Select value={confidenceFilter} onValueChange={setConfidenceFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="high">High (80%+)</SelectItem>
                  <SelectItem value="medium">Medium (60-79%)</SelectItem>
                  <SelectItem value="low">Low (&lt;60%)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Clear Filters */}
            <Button variant="outline" className="w-full">
              <Icon name="filter_alt_off" className="mr-2" />
              Clear All Filters
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-[1200px] mx-auto">
            {/* Header */}
            <div className="mb-6">
              <h1 className="text-3xl font-black mb-2">Action Items Dashboard</h1>
              <p className="text-muted-foreground">
                Review and manage tasks extracted from your recent meeting transcripts
              </p>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold">10</div>
                  <div className="text-xs text-muted-foreground">Total Items</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-yellow-600">7</div>
                  <div className="text-xs text-muted-foreground">Pending</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-green-600">3</div>
                  <div className="text-xs text-muted-foreground">Completed</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-red-600">5</div>
                  <div className="text-xs text-muted-foreground">Needs Review</div>
                </CardContent>
              </Card>
            </div>

            {/* Table */}
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50 dark:bg-slate-900">
                      <TableHead className="w-[40px]">
                        <Checkbox />
                      </TableHead>
                      <TableHead className="w-[400px]">Task Description</TableHead>
                      <TableHead>Owner</TableHead>
                      <TableHead>Deadline</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead>Risks</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {actionItems.map((item) => (
                      <TableRow key={item.id} className={item.isComplete ? "opacity-50" : ""}>
                        <TableCell>
                          <Checkbox checked={item.isComplete} />
                        </TableCell>
                        <TableCell className="font-medium">
                          <div className="flex items-start gap-2">
                            {item.isComplete && <Icon name="check_circle" className="text-green-600 text-sm flex-shrink-0 mt-0.5" />}
                            <div>
                              <div className={item.isComplete ? "line-through" : ""}>{item.description}</div>
                              <div className="text-xs text-muted-foreground mt-1">
                                From: {item.meetingTitle}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {item.owner ? (
                            <div className="flex items-center gap-2">
                              <div className="size-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                                {item.owner.split(' ').map(n => n[0]).join('')}
                              </div>
                              <span className="text-sm">{item.owner}</span>
                            </div>
                          ) : (
                            <span className="text-sm text-muted-foreground italic">Unassigned</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {item.deadline ? (
                            <div className="flex items-center gap-1.5 text-sm">
                              <Icon name="calendar_today" className="text-xs text-muted-foreground" />
                              {new Date(item.deadline).toLocaleDateString()}
                            </div>
                          ) : (
                            <span className="text-sm text-muted-foreground italic">TBD</span>
                          )}
                        </TableCell>
                        <TableCell>{getPriorityBadge(item.priority)}</TableCell>
                        <TableCell>{getConfidenceBadge(item.confidence, item.confidenceScore)}</TableCell>
                        <TableCell>
                          {item.riskFlags > 0 ? (
                            <Badge variant="destructive" className="gap-1">
                              <Icon name="warning" className="text-xs" />
                              {item.riskFlags}
                            </Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                              <Icon name="edit" className="text-sm" />
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                              <Icon name="more_vert" className="text-sm" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
