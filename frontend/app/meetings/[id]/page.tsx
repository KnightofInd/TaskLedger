"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/shared/Header";
import { Icon } from "@/components/shared/Icon";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { apiClient, Meeting, ActionItem } from "@/lib/api";

export default function MeetingDetailPage() {
  const params = useParams();
  const meetingId = params.id as string;
  
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMeetingData() {
      try {
        const [meetingData, itemsResponse] = await Promise.all([
          apiClient.getMeeting(meetingId),
          apiClient.getMeetingActionItems(meetingId)
        ]);
        setMeeting(meetingData);
        setActionItems(itemsResponse.action_items);
      } catch (error) {
        console.error("Failed to fetch meeting data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchMeetingData();
  }, [meetingId]);

  const handleToggleComplete = async (itemId: string, isComplete: boolean) => {
    try {
      await apiClient.updateActionItem(itemId, { is_complete: !isComplete });
      setActionItems(items => 
        items.map(item => 
          item.id === itemId ? { ...item, is_complete: !isComplete } : item
        )
      );
    } catch (error) {
      console.error("Failed to update action item:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <main className="max-w-[1440px] mx-auto p-6 lg:p-10 w-full">
          <Card className="shadow-sm">
            <CardContent className="p-12 text-center">
              <Icon name="progress_activity" className="text-4xl text-primary animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading meeting details...</p>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <main className="max-w-[1440px] mx-auto p-6 lg:p-10 w-full">
          <Card className="shadow-sm">
            <CardContent className="p-12 text-center">
              <Icon name="error" className="text-4xl text-red-600 mx-auto mb-4" />
              <p className="text-muted-foreground">Meeting not found</p>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }

  const statistics = {
    totalItems: actionItems.length,
    completeItems: actionItems.filter(item => item.is_complete).length,
    pendingItems: actionItems.filter(item => !item.is_complete).length,
    highPriority: actionItems.filter(item => item.priority === "HIGH").length,
    mediumPriority: actionItems.filter(item => item.priority === "MEDIUM").length,
    lowPriority: actionItems.filter(item => item.priority === "LOW").length
  };
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      
      <main className="max-w-[1440px] mx-auto p-6 lg:p-10 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Sidebar: Metadata */}
          <aside className="lg:col-span-3 space-y-6">
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-6">
                  <Badge className="bg-green-100 text-green-700 hover:bg-green-100 text-[10px] font-bold uppercase tracking-widest">
                    Processed
                  </Badge>
                  <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                    <Icon name="edit" className="text-lg" />
                  </Button>
                </div>
                
                <h1 className="text-3xl font-black leading-tight mb-2">{meeting.meeting_title}</h1>
                <p className="text-sm text-muted-foreground mb-6 flex items-center gap-2">
                  <Icon name="calendar_today" className="text-sm" />
                  {new Date(meeting.meeting_date).toLocaleDateString()}
                </p>

                <div className="space-y-4">
                  <div>
                    <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Participants ({meeting.participants?.length || 0})
                    </p>
                    <div className="flex flex-col gap-3">
                      {meeting.participants?.map((participant, idx) => (
                        <div key={idx} className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                            {participant.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <p className="text-xs font-bold">{participant}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-3">
                      Confidence Score
                    </p>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-bold">{Math.round(meeting.total_confidence * 100)}%</span>
                        <span className="text-muted-foreground">Overall</span>
                      </div>
                      <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-600"
                          style={{ width: `${meeting.total_confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <Button variant="outline" className="w-full" size="sm">
                    <Icon name="ios_share" className="mr-2" />
                    Export Meeting
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Statistics Card */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <h3 className="text-sm font-bold mb-4">Statistics</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Actions</span>
                    <span className="font-bold">{statistics.totalItems}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Completed</span>
                    <span className="font-bold text-green-600">{statistics.completeItems}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Pending</span>
                    <span className="font-bold text-yellow-600">{statistics.pendingItems}</span>
                  </div>
                  <div className="pt-3 border-t space-y-2">
                    <div className="flex justify-between">
                      <Badge className="bg-red-100 text-red-700 text-xs">HIGH</Badge>
                      <span className="font-bold">{statistics.highPriority}</span>
                    </div>
                    <div className="flex justify-between">
                      <Badge className="bg-amber-100 text-amber-700 text-xs">MEDIUM</Badge>
                      <span className="font-bold">{statistics.mediumPriority}</span>
                    </div>
                    <div className="flex justify-between">
                      <Badge variant="secondary" className="text-xs">LOW</Badge>
                      <span className="font-bold">{statistics.lowPriority}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </aside>

          {/* Main Content */}
          <div className="lg:col-span-9 space-y-6">
            {/* Action Items Table */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-black">Action Items</h2>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Icon name="filter_list" className="mr-2" />
                      Filter
                    </Button>
                    <Button variant="outline" size="sm">
                      <Icon name="sort" className="mr-2" />
                      Sort
                    </Button>
                  </div>
                </div>

                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50 dark:bg-slate-900">
                      <TableHead className="w-[40px]">
                        <Checkbox />
                      </TableHead>
                      <TableHead className="w-[400px]">Description</TableHead>
                      <TableHead>Owner</TableHead>
                      <TableHead>Deadline</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {actionItems.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <Checkbox 
                            checked={item.is_complete} 
                            onCheckedChange={() => handleToggleComplete(item.id, item.is_complete)}
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          <div>
                            {item.description}
                            {item.risk_flags && item.risk_flags.length > 0 && (
                              <div className="flex items-center gap-1 mt-1">
                                <Icon name="warning" className="text-xs text-red-600" />
                                <span className="text-xs text-red-600">{item.risk_flags.length} risk flags</span>
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="size-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                              {item.owner?.split(' ').map(n => n[0]).join('') || 'U'}
                            </div>
                            <span className="text-sm">{item.owner || 'Unassigned'}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {item.deadline ? new Date(item.deadline).toLocaleDateString() : 'No deadline'}
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            item.priority === "HIGH" ? "bg-red-100 text-red-700" :
                            item.priority === "MEDIUM" ? "bg-amber-100 text-amber-700" :
                            ""
                          }>
                            {item.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            item.confidence_score * 100 >= 85 ? "bg-green-100 text-green-700" :
                            item.confidence_score * 100 >= 70 ? "bg-yellow-100 text-yellow-700" :
                            "bg-red-100 text-red-700"
                          }>
                            {Math.round(item.confidence_score * 100)}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {item.clarification_questions && item.clarification_questions.length > 0 && (
                              <Button size="sm" variant="ghost" className="h-8 px-2">
                                <Icon name="help" className="text-sm text-primary" />
                              </Button>
                            )}
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

            {/* Original Transcript (Collapsible) */}
            <Card className="shadow-sm">
              <CardContent className="p-6">
                <details>
                  <summary className="font-bold text-lg cursor-pointer flex items-center gap-2 mb-4">
                    <Icon name="description" />
                    Original Transcript
                  </summary>
                  <div className="bg-slate-50 dark:bg-slate-900 p-4 rounded-lg text-sm font-mono leading-relaxed whitespace-pre-wrap">
                    {meeting.meeting_text}
                  </div>
                </details>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
