import { useEffect, useState } from 'react';
import { Deal } from '@/types';
import { getDeals } from '@/services/api';
import './shared.css';

export const BusinessHealth = () => {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const dealsData = await getDeals();
        setDeals(dealsData);
      } catch (error) {
        console.error('Failed to load deals:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const activeDeals = deals.filter((d) => d.status === 'active').length;
  const totalValue = deals
    .filter((d) => d.status !== 'closed')
    .reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Business Health</h1>
        <p className="page-subtitle">Pipeline & Deal Status</p>
      </div>

      <div className="stats-section">
        <div className="stat-box">
          <div className="stat-label">Active Deals</div>
          <div className="stat-value">{activeDeals}</div>
          <div className="stat-detail">{deals.length} total</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Pipeline Value</div>
          <div className="stat-value">${(totalValue / 1000000).toFixed(1)}M</div>
          <div className="stat-detail">In progress</div>
        </div>
      </div>

      {!loading && (
        <div className="deals-section">
          <h2>All Deals</h2>
          <div className="deals-list">
            {deals.map((deal) => (
              <div key={deal.id} className={`deal-card status-${deal.status}`}>
                <div className="deal-status-badge">{deal.status.toUpperCase()}</div>
                <h3>{deal.clientName}</h3>
                <p className="deal-address">{deal.address}</p>
                <div className="deal-footer">
                  <span className="deal-value">${(deal.value / 1000).toFixed(0)}k</span>
                  <span className="deal-updated">{formatTime(deal.lastUpdate)}</span>
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
