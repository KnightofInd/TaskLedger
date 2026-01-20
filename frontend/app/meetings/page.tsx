"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/shared/Header";
import { Icon } from "@/components/shared/Icon";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { apiClient, Meeting } from "@/lib/api";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMeetings() {
      try {
        const response = await apiClient.listMeetings(0, 50);
        setMeetings(response.meetings);
      } catch (error) {
        console.error("Failed to fetch meetings:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchMeetings();
  }, []);
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex flex-1 justify-center py-8">
        <div className="layout-content-container flex flex-col max-w-[1100px] flex-1 px-4">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-slate-900 dark:text-white text-3xl font-black leading-tight tracking-tight mb-1">
                All Meetings
              </h1>
              <p className="text-slate-600 dark:text-slate-400 text-sm">
                Browse and manage all your meeting transcripts
              </p>
            </div>
            <Button asChild>
              <Link href="/meetings/new">
                <Icon name="add" className="mr-2" />
                New Meeting
              </Link>
            </Button>
          </div>

          {/* Meetings Grid */}
          <div className="grid grid-cols-1 gap-4">
            {loading ? (
              <Card className="shadow-sm">
                <CardContent className="p-12 text-center">
                  <Icon name="progress_activity" className="text-4xl text-primary animate-spin mx-auto mb-4" />
                  <p className="text-muted-foreground">Loading meetings...</p>
                </CardContent>
              </Card>
            ) : meetings.length > 0 ? (
              meetings.map((meeting) => (
                <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                  <Card className="shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-slate-900 dark:text-white text-lg font-bold">
                              {meeting.meeting_title}
                            </h3>
                            <Badge 
                              variant="default"
                              className="bg-green-100 text-green-700 hover:bg-green-100"
                            >
                              Processed
                            </Badge>
                          </div>
                          
                          <div className="flex items-center gap-6 text-sm text-slate-600 dark:text-slate-400 mb-4">
                            <div className="flex items-center gap-1.5">
                              <Icon name="calendar_today" className="text-xs" />
                              <span>{new Date(meeting.meeting_date).toLocaleDateString()}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Icon name="people" className="text-xs" />
                              <span>{meeting.participants?.length || 0} participants</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Icon name="task" className="text-xs" />
                              <span>{meeting.action_items?.length || 0} action items</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                              Confidence:
                            </span>
                            <div className="flex-1 max-w-[200px] h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${
                                  meeting.total_confidence * 100 >= 85 ? "bg-green-600" : 
                                  meeting.total_confidence * 100 >= 70 ? "bg-yellow-600" : 
                                  "bg-red-600"
                                }`}
                                style={{ width: `${meeting.total_confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-bold text-slate-900 dark:text-white">
                              {Math.round(meeting.total_confidence * 100)}%
                            </span>
                          </div>
                        </div>

                        <Button size="sm" variant="ghost">
                          <Icon name="arrow_forward" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))
            ) : (
              <Card className="shadow-sm">
                <CardContent className="p-12 text-center">
                  <div className="flex flex-col items-center gap-4">
                    <div className="size-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                      <Icon name="meeting_room" className="text-4xl text-slate-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold mb-1">No meetings yet</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Get started by processing your first meeting transcript
                      </p>
                      <Button asChild>
                        <Link href="/meetings/new">
                          <Icon name="add" className="mr-2" />
                          Create First Meeting
                        </Link>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
