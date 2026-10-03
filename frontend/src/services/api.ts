import { Brief, Agent, Approval, Deal, BusinessMetrics } from '@/types';
import { mockBriefs, mockAgents, mockApprovals, mockDeals, mockMetrics } from '@/mocks/mockData';

const API_BASE = '/api';

// Helper to swap mock/real endpoints later
const useMockData = true;

// ── Briefs ──
export async function getBriefs(): Promise<Brief[]> {
  if (useMockData) {
    return new Promise((resolve) => setTimeout(() => resolve(mockBriefs), 300));
  }
  const res = await fetch(`${API_BASE}/briefs`);
  return res.json();
}

export async function getBrief(id: string): Promise<Brief> {
  if (useMockData) {
    const brief = mockBriefs.find((b) => b.id === id);
    if (!brief) throw new Error('Brief not found');
    return new Promise((resolve) => setTimeout(() => resolve(brief), 200));
  }
  const res = await fetch(`${API_BASE}/briefs/${id}`);
  return res.json();
}

// ── Agents ──
export async function getAgents(): Promise<Agent[]> {
  if (useMockData) {
    return new Promise((resolve) => setTimeout(() => resolve(mockAgents), 300));
  }
  const res = await fetch(`${API_BASE}/agents`);
  return res.json();
}

export async function getAgent(id: string): Promise<Agent> {
  if (useMockData) {
    const agent = mockAgents.find((a) => a.id === id);
    if (!agent) throw new Error('Agent not found');
    return new Promise((resolve) => setTimeout(() => resolve(agent), 200));
  }
  const res = await fetch(`${API_BASE}/agents/${id}`);
  return res.json();
}

// ── Approvals ──
export async function getApprovals(): Promise<Approval[]> {
  if (useMockData) {
    return new Promise((resolve) => setTimeout(() => resolve(mockApprovals), 300));
  }
  const res = await fetch(`${API_BASE}/approvals`);
  return res.json();
}

export async function approveApproval(id: string): Promise<Approval> {
  if (useMockData) {
    const approval = mockApprovals.find((a) => a.id === id);
    if (!approval) throw new Error('Approval not found');
    approval.status = 'approved';
    return new Promise((resolve) => setTimeout(() => resolve(approval), 500));
  }
  const res = await fetch(`${API_BASE}/approvals/${id}/approve`, { method: 'POST' });
  return res.json();
}

export async function denyApproval(id: string): Promise<Approval> {
  if (useMockData) {
    const approval = mockApprovals.find((a) => a.id === id);
    if (!approval) throw new Error('Approval not found');
    approval.status = 'denied';
    return new Promise((resolve) => setTimeout(() => resolve(approval), 500));
  }
  const res = await fetch(`${API_BASE}/approvals/${id}/deny`, { method: 'POST' });
  return res.json();
}

// ── Deals ──
export async function getDeals(): Promise<Deal[]> {
  if (useMockData) {
    return new Promise((resolve) => setTimeout(() => resolve(mockDeals), 300));
  }
  const res = await fetch(`${API_BASE}/deals`);
  return res.json();
}

export async function getDeal(id: string): Promise<Deal> {
  if (useMockData) {
    const deal = mockDeals.find((d) => d.id === id);
    if (!deal) throw new Error('Deal not found');
    return new Promise((resolve) => setTimeout(() => resolve(deal), 200));
  }
  const res = await fetch(`${API_BASE}/deals/${id}`);
  return res.json();
}

// ── Metrics ──
export async function getMetrics(): Promise<BusinessMetrics> {
  if (useMockData) {
    return new Promise((resolve) => setTimeout(() => resolve(mockMetrics), 300));
  }
  const res = await fetch(`${API_BASE}/metrics`);
  return res.json();
}
