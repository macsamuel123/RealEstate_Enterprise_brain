export type RingState = 'idle' | 'listening' | 'speaking';

export interface Brief {
  id: string;
  title: string;
  content: string;
  timestamp: Date;
  priority: 'high' | 'medium' | 'low';
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'active' | 'idle' | 'error';
  lastActive?: Date;
}

export interface Approval {
  id: string;
  type: 'email' | 'message' | 'action';
  description: string;
  preview: string;
  timestamp: Date;
  status: 'pending' | 'approved' | 'denied';
}

export interface Deal {
  id: string;
  clientName: string;
  address: string;
  status: 'new' | 'active' | 'closed';
  value: number;
  lastUpdate: Date;
}

export interface BusinessMetrics {
  leadsToday: number;
  activeDeal: number;
  approvalsPending: number;
  agentsActive: number;
}
