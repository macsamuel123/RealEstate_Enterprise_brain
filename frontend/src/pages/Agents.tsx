import { useEffect, useState } from 'react';
import { Agent } from '@/types';
import { getAgents } from '@/services/api';
import './shared.css';

export const Agents = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const agentsData = await getAgents();
        setAgents(agentsData);
      } catch (error) {
        console.error('Failed to load agents:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const active = agents.filter((a) => a.status === 'active').length;
  const idle = agents.filter((a) => a.status === 'idle').length;
  const error = agents.filter((a) => a.status === 'error').length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Agents</h1>
        <p className="page-subtitle">AI Agent Status</p>
      </div>

      <div className="stats-section">
        <div className="stat-box">
          <div className="stat-label">Active</div>
          <div className="stat-value">{active}</div>
          <div className="stat-detail">Agents running</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Idle</div>
          <div className="stat-value">{idle}</div>
          <div className="stat-detail">Standby</div>
        </div>
        {error > 0 && (
          <div className="stat-box">
            <div className="stat-label">Errors</div>
            <div className="stat-value" style={{ color: '#e74c3c' }}>
              {error}
            </div>
            <div className="stat-detail">Needs attention</div>
          </div>
        )}
      </div>

      {!loading && (
        <div className="agents-section">
          <h2>All Agents</h2>
          <div className="agents-list">
            {agents.map((agent) => (
              <div key={agent.id} className={`agent-card status-${agent.status}`}>
                <div className="agent-status-badge">{agent.status.toUpperCase()}</div>
                <h3>{agent.name}</h3>
                <p className="agent-role">{agent.role}</p>
                <div className="agent-footer">
                  <span className="agent-id">{agent.id}</span>
                  <span className="agent-updated">
                    {agent.lastActive ? formatTime(agent.lastActive) : 'Never'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

function formatTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return `${Math.floor(diffMins / 1440)}d ago`;
}
