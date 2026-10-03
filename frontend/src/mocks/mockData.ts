import { Brief, Agent, Approval, Deal, BusinessMetrics } from '@/types';

// Getty Group pilot customer mock data
export const mockBriefs: Brief[] = [
  {
    id: '1',
    title: 'Morning Market Update',
    content: '3 new listings in NW Calgary. Average days-on-market down 2 days YoY. Buyer inquiry spike in west communities.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    priority: 'high',
  },
  {
    id: '2',
    title: 'Follow-up Reminders',
    content: 'Shawn has 5 pending follow-ups. Mr. and Mrs. Chen interested in 123 Aspen Ridge Drive. Carlos Lopez seeking investment property.',
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    priority: 'high',
  },
  {
    id: '3',
    title: 'Team Performance',
    content: 'Jessica: 4 showings scheduled. Mark: 2 new leads qualified. Rachel: 1 closing coordination in progress.',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    priority: 'medium',
  },
];

export const mockAgents: Agent[] = [
  {
    id: 'lead-qualifier',
    name: 'Lead Qualifier',
    role: 'Intake & Qualification',
    status: 'active',
    lastActive: new Date(Date.now() - 5 * 60 * 1000),
  },
  {
    id: 'follow-up',
    name: 'Follow-up Master',
    role: 'Lead Nurture',
    status: 'active',
    lastActive: new Date(Date.now() - 15 * 60 * 1000),
  },
  {
    id: 'email-composer',
    name: 'Email Composer',
    role: 'Communication',
    status: 'idle',
    lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000),
  },
  {
    id: 'calendar-manager',
    name: 'Calendar Manager',
    role: 'Scheduling',
    status: 'active',
    lastActive: new Date(Date.now() - 20 * 60 * 1000),
  },
  {
    id: 'market-analyst',
    name: 'Market Analyst',
    role: 'Analytics & Insights',
    status: 'idle',
    lastActive: new Date(Date.now() - 1 * 60 * 60 * 1000),
  },
];

export const mockApprovals: Approval[] = [
  {
    id: 'app-1',
    type: 'email',
    description: 'Send follow-up to Chen family',
    preview: 'Hi Mr. & Mrs. Chen, Thank you for your interest in 123 Aspen Ridge Drive. I wanted to follow up...',
    timestamp: new Date(Date.now() - 10 * 60 * 1000),
    status: 'pending',
  },
  {
    id: 'app-2',
    type: 'message',
    description: 'Schedule showing for Carlos Lopez',
    preview: 'Can you show the investment property at 456 Commerce Drive on Thursday at 2pm?',
    timestamp: new Date(Date.now() - 25 * 60 * 1000),
    status: 'pending',
  },
  {
    id: 'app-3',
    type: 'action',
    description: 'Send market report to mailing list',
    preview: 'Weekly market update with 15 new listings and market trends analysis',
    timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
    status: 'pending',
  },
];

export const mockDeals: Deal[] = [
  {
    id: 'deal-1',
    clientName: 'Mr. & Mrs. Chen',
    address: '123 Aspen Ridge Drive, Calgary',
    status: 'active',
    value: 850000,
    lastUpdate: new Date(Date.now() - 30 * 60 * 1000),
  },
  {
    id: 'deal-2',
    clientName: 'Carlos Lopez',
    address: '456 Commerce Drive, Calgary',
    status: 'active',
    value: 650000,
    lastUpdate: new Date(Date.now() - 2 * 60 * 60 * 1000),
  },
  {
    id: 'deal-3',
    clientName: 'Sarah Mitchell',
    address: '789 Heritage Way, Calgary',
    status: 'new',
    value: 1200000,
    lastUpdate: new Date(Date.now() - 1 * 60 * 60 * 1000),
  },
  {
    id: 'deal-4',
    clientName: 'Robert Johnson',
    address: 'Sold: 321 Riverside Terrace',
    status: 'closed',
    value: 750000,
    lastUpdate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
  },
];

export const mockMetrics: BusinessMetrics = {
  leadsToday: 7,
  activeDeal: 3,
  approvalsPending: 3,
  agentsActive: 2,
};
