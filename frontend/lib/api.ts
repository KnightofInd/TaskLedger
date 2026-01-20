const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface MeetingInput {
  meeting_text: string;
  participants: string[];
  meeting_title?: string;
  meeting_date?: string;
}

export interface ActionItem {
  id: string;
  description: string;
  owner: string | null;
  deadline: string | null;
  priority: string;
  confidence: string;
  confidence_score: number;
  is_complete: boolean;
  dependencies?: string[];
  context?: string;
  risk_flags?: RiskFlag[];
  clarification_questions?: ClarificationQuestion[];
}

export interface RiskFlag {
  id?: number;
  risk_type: string;
  description: string;
  severity: string;
  suggested_clarification?: string;
}

export interface ClarificationQuestion {
  id: number;
  question: string;
  field: string;
  priority: string;
  answer?: string;
  answered_at?: string;
}

export interface Meeting {
  id: string;
  meeting_title: string;
  meeting_text?: string;
  meeting_date: string;
  participants: string[];
  processed_at: string;
  total_confidence: number;
  action_items?: ActionItem[];
}

export interface MeetingStatistics {
  total_items: number;
  complete_items: number;
  priority_breakdown: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Meeting endpoints
  async createMeeting(data: MeetingInput) {
    return this.request<{ id: string; meeting_id: string }>('/meetings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listMeetings(skip = 0, limit = 50) {
    return this.request<{ meetings: Meeting[]; count: number }>(
      `/meetings?skip=${skip}&limit=${limit}`
    );
  }

  async getMeeting(meetingId: string) {
    return this.request<Meeting>(`/meetings/${meetingId}`);
  }

  async deleteMeeting(meetingId: string) {
    return this.request<void>(`/meetings/${meetingId}`, {
      method: 'DELETE',
    });
  }

  // Action item endpoints
  async getMeetingActionItems(meetingId: string) {
    return this.request<{ action_items: ActionItem[]; count: number }>(
      `/meetings/${meetingId}/action-items`
    );
  }

  async getActionItem(actionItemId: string) {
    return this.request<ActionItem>(`/action-items/${actionItemId}`);
  }

  async updateActionItem(
    actionItemId: string,
    data: {
      owner?: string;
      deadline?: string;
      priority?: string;
      is_complete?: boolean;
    }
  ) {
    return this.request<ActionItem>(`/action-items/${actionItemId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async answerClarification(
    actionItemId: string,
    data: { question_id: number; answer: string }
  ) {
    return this.request<ClarificationQuestion>(
      `/action-items/${actionItemId}/clarify`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string }>('/health');
  }
}

export const apiClient = new APIClient(API_BASE_URL);
