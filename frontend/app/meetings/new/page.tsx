"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/shared/Header";
import { Icon } from "@/components/shared/Icon";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api";

export default function NewMeetingPage() {
  const router = useRouter();
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().split('T')[0]);
  const [transcript, setTranscript] = useState("");
  const [participants, setParticipants] = useState<string[]>(["Sarah Chen", "Michael Torres", "Emma Davis"]);
  const [newParticipant, setNewParticipant] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addParticipant = () => {
    if (newParticipant.trim() && !participants.includes(newParticipant.trim())) {
      setParticipants([...participants, newParticipant.trim()]);
      setNewParticipant("");
    }
  };

  const removeParticipant = (name: string) => {
    setParticipants(participants.filter(p => p !== name));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addParticipant();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    setError(null);
    
    try {
      const response = await apiClient.createMeeting({
        meeting_text: transcript,
        participants,
        meeting_title: meetingTitle,
        meeting_date: meetingDate
      });
      
      // Redirect to the meeting detail page
      router.push(`/meetings/${response.meeting_id}`);
    } catch (err) {
      console.error("Failed to create meeting:", err);
      setError(err instanceof Error ? err.message : "Failed to process meeting");
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      
      <main className="flex-1 flex flex-col items-center py-12 px-6">
        {/* Page Header */}
        <div className="max-w-4xl w-full mb-10 text-center">
          <h1 className="text-4xl font-black tracking-tight mb-3">New Meeting Analysis</h1>
          <p className="text-slate-600 dark:text-slate-400 text-lg">
            Input your transcript and let AI handle the action items, assignments, and follow-ups.
          </p>
        </div>

        {/* Main Form Container */}
        <form onSubmit={handleSubmit} className="max-w-4xl w-full">
          <Card className="shadow-lg border-slate-200 dark:border-slate-800">
            <CardContent className="p-8 space-y-8">
              {/* Metadata Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Meeting Title
                  </label>
                  <Input
                    value={meetingTitle}
                    onChange={(e) => setMeetingTitle(e.target.value)}
                    className="h-12"
                    placeholder="e.g. Q4 Growth Strategy Sync"
                    required
                  />
                </div>
                
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Date & Time
                  </label>
                  <div className="relative">
                    <Icon 
                      name="calendar_today" 
                      className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600"
                    />
                    <Input
                      type="date"
                      value={meetingDate}
                      onChange={(e) => setMeetingDate(e.target.value)}
                      className="h-12 pl-12"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Participant Chip Input */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  Participants
                </label>
                <div className="flex flex-wrap gap-2 p-3 min-h-[56px] rounded-lg border border-slate-300 dark:border-slate-700 items-center bg-white dark:bg-slate-900">
                  {/* Chips */}
                  {participants.map((participant) => (
                    <Badge
                      key={participant}
                      variant="secondary"
                      className="flex items-center gap-2 bg-primary/10 text-primary dark:bg-primary/20 px-3 py-1.5 text-sm font-semibold hover:bg-primary/15"
                    >
                      <Icon name="person" className="text-sm" />
                      {participant}
                      <button
                        type="button"
                        onClick={() => removeParticipant(participant)}
                        className="hover:text-red-500 transition-colors"
                      >
                        <Icon name="close" className="text-sm" />
                      </button>
                    </Badge>
                  ))}
                  
                  {/* Input for new participant */}
                  <input
                    type="text"
                    value={newParticipant}
                    onChange={(e) => setNewParticipant(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 min-w-[120px] bg-transparent border-none outline-none text-sm"
                    placeholder="Add participant..."
                  />
                </div>
              </div>

              {/* Transcript Textarea */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Meeting Transcript
                  </label>
                  <span className="text-xs text-slate-500">
                    {transcript.length} characters
                  </span>
                </div>
                <Textarea
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="min-h-[400px] resize-y font-mono text-base leading-relaxed !text-slate-900 dark:!text-slate-100 [&]:text-slate-900 dark:[&]:text-slate-100"
                  style={{ color: 'rgb(15 23 42)' }}
                  placeholder="Paste your meeting transcript or notes here...

Example:
Sarah: Let's discuss the Q4 roadmap. We need to finalize the feature list by next Friday.
Michael: I'll prepare the technical specs. Can we get design mockups by Wednesday?
Emma: Sure, I'll have the designs ready by Wednesday EOD..."
                  required
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-400 mb-4">
                  <Icon name="info" className="text-base" />
                  <span>AI will extract action items, owners, and deadlines automatically</span>
                </div>
                
                <div className="flex items-center gap-3">
                  <Button 
                    type="submit" 
                    size="lg"
                    disabled={isProcessing || !transcript.trim() || !meetingTitle.trim()}
                    className="bg-primary hover:bg-primary/90 font-bold px-6 h-11"
                    style={{ display: 'inline-flex', color: '#4d09d6' }}
                  >
                    {isProcessing ? (
                      <>
                        <Icon name="progress_activity" className="mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Icon name="auto_awesome" className="mr-2" />
                        Process Meeting
                      </>
                    )}
                  </Button>
                  
                  <Button 
                    type="button" 
                    variant="outline" 
                    size="lg"
                    className="px-6 h-11"
                    style={{ display: 'inline-flex' }}
                  >
                    <Icon name="draft" className="mr-2" />
                    Save Draft
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Processing Status */}
          {isProcessing && (
            <Card className="mt-6 shadow-lg border-primary/20 bg-primary/5">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <Icon name="psychology" className="text-primary animate-pulse" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg mb-2">AI Processing in Progress</h3>
                    <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                      <div className="flex items-center gap-2">
                        <div className="size-1.5 rounded-full bg-green-500" />
                        <span>Extracting action items from transcript...</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="size-1.5 rounded-full bg-yellow-500 animate-pulse" />
                        <span>Identifying owners and deadlines...</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="size-1.5 rounded-full bg-slate-300" />
                        <span>Validating completeness and flagging risks...</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Message */}
          {error && (
            <Card className="mt-6 shadow-lg border-red-500/20 bg-red-50 dark:bg-red-950/20">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <Icon name="error" className="text-red-600 text-2xl flex-shrink-0" />
                  <div>
                    <h3 className="font-bold text-lg text-red-900 dark:text-red-100 mb-1">Processing Failed</h3>
                    <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </form>
      </main>
    </div>
  );
}
