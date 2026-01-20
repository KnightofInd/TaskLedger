"use client";

import { useState } from "react";
import { Icon } from "@/components/shared/Icon";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";

interface ClarificationQuestion {
  id: number;
  question: string;
  field: string;
  priority: string;
  answer?: string;
}

interface ClarificationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  actionItem: {
    id: string;
    description: string;
    owner?: string;
    deadline?: string;
    priority: string;
    confidence: string;
  };
  questions: ClarificationQuestion[];
  onSubmit: (answers: Record<number, string>) => void;
}

export function ClarificationSheet({ 
  open, 
  onOpenChange, 
  actionItem, 
  questions,
  onSubmit 
}: ClarificationSheetProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    await onSubmit(answers);
    setIsSubmitting(false);
    onOpenChange(false);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "high": return "text-red-600";
      case "medium": return "text-amber-600";
      default: return "text-slate-600";
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[480px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <div className="flex items-start gap-3 mb-2">
            <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Icon name="help" className="text-primary text-xl" />
            </div>
            <div className="flex-1">
              <SheetTitle className="text-xl font-black mb-1">Clarification Needed</SheetTitle>
              <SheetDescription>
                Help improve this action item by answering the questions below
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Action Item Context */}
          <div className="bg-slate-50 dark:bg-slate-900 p-4 rounded-lg space-y-3">
            <div>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                Action Item
              </p>
              <p className="text-sm font-medium">{actionItem.description}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-200 dark:border-slate-700">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Owner</p>
                <p className="text-sm font-medium">
                  {actionItem.owner || <span className="italic text-muted-foreground">Unassigned</span>}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Deadline</p>
                <p className="text-sm font-medium">
                  {actionItem.deadline || <span className="italic text-muted-foreground">TBD</span>}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Priority</p>
                <Badge 
                  variant={actionItem.priority === "HIGH" ? "destructive" : "secondary"}
                  className="text-xs"
                >
                  {actionItem.priority}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                <Badge 
                  className={
                    actionItem.confidence === "HIGH" ? "bg-green-100 text-green-700" :
                    actionItem.confidence === "MEDIUM" ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  }
                >
                  {actionItem.confidence}
                </Badge>
              </div>
            </div>
          </div>

          {/* Questions */}
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
                Questions ({questions.length})
              </h3>
              <span className="text-xs text-muted-foreground">
                {Object.keys(answers).length} of {questions.length} answered
              </span>
            </div>

            {questions.map((question, index) => (
              <div key={question.id} className="space-y-2">
                <div className="flex items-start gap-2">
                  <Badge variant="outline" className="text-xs font-mono mt-0.5">
                    Q{index + 1}
                  </Badge>
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <Label htmlFor={`question-${question.id}`} className="text-sm font-medium leading-tight">
                        {question.question}
                      </Label>
                      <Badge 
                        variant="secondary" 
                        className={`text-[10px] ${getPriorityColor(question.priority)} flex-shrink-0`}
                      >
                        {question.priority} priority
                      </Badge>
                    </div>
                    
                    {question.field === "description" ? (
                      <Textarea
                        id={`question-${question.id}`}
                        value={answers[question.id] || ""}
                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                        placeholder="Type your answer here..."
                        className="min-h-[80px] text-sm"
                      />
                    ) : (
                      <Input
                        id={`question-${question.id}`}
                        type={question.field === "deadline" ? "date" : "text"}
                        value={answers[question.id] || ""}
                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                        placeholder={
                          question.field === "owner" ? "Enter name..." :
                          question.field === "deadline" ? "Select date..." :
                          "Type your answer..."
                        }
                        className="text-sm"
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-6 border-t border-border sticky bottom-0 bg-background pb-6">
            <Button 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={isSubmitting || Object.keys(answers).length === 0}
              className="flex-1 bg-primary hover:bg-primary/90"
            >
              {isSubmitting ? (
                <>
                  <Icon name="progress_activity" className="mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Icon name="check" className="mr-2" />
                  Submit Answers
                </>
              )}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
