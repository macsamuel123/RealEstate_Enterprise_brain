import { useEffect, useState } from 'react';
import { Brief } from '@/types';
import { getBriefs } from '@/services/api';
import './shared.css';

export const Today = () => {
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const briefsData = await getBriefs();
        setBriefs(briefsData);
      } catch (error) {
        console.error('Failed to load briefs:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Today</h1>
        <p className="page-subtitle">Daily Briefing & Agenda</p>
      </div>

      <div className="stats-section">
        <div className="stat-box">
          <div className="stat-label">Items</div>
          <div className="stat-value">{briefs.length}</div>
          <div className="stat-detail">Today's agenda</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">High Priority</div>
          <div className="stat-value">{briefs.filter((b) => b.priority === 'high').length}</div>
          <div className="stat-detail">Needs attention</div>
        </div>
      </div>

      {!loading && (
        <div className="briefs-section">
          <h2>Daily Briefs</h2>
          <div className="briefs-list">
            {briefs.map((brief) => (
              <div
                key={brief.id}
                className={`brief-card status-${brief.priority === 'high' ? 'urgent' : 'normal'}`}
              >
                <div className="brief-header">
                  <div>
                    <h3>{brief.title}</h3>
                    <p className="brief-content">{brief.content}</p>
                  </div>
                  <div className="brief-meta">
                    <span className={`priority-badge priority-${brief.priority}`}>
                      {brief.priority.toUpperCase()}
                    </span>
                    <span className="brief-time">{formatTime(brief.timestamp)}</span>
                  </div>
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

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  return `${Math.floor(diffMins / 1440)}d ago`;
}
