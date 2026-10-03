import { useEffect, useState } from 'react';
import { Approval } from '@/types';
import { getApprovals, approveApproval, denyApproval } from '@/services/api';
import './shared.css';

export const Approvals = () => {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      const approvalsData = await getApprovals();
      setApprovals(approvalsData);
    } catch (error) {
      console.error('Failed to load approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    setProcessing(id);
    try {
      await approveApproval(id);
      setApprovals((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'approved' } : a))
      );
    } catch (error) {
      console.error('Failed to approve:', error);
    } finally {
      setProcessing(null);
    }
  };

  const handleDeny = async (id: string) => {
    setProcessing(id);
    try {
      await denyApproval(id);
      setApprovals((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'denied' } : a))
      );
    } catch (error) {
      console.error('Failed to deny:', error);
    } finally {
      setProcessing(null);
    }
  };

  const pending = approvals.filter((a) => a.status === 'pending');
  const processed = approvals.filter((a) => a.status !== 'pending');

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Approvals</h1>
        <p className="page-subtitle">Pending Decisions</p>
      </div>

      <div className="stats-section">
        <div className="stat-box">
          <div className="stat-label">Pending</div>
          <div className="stat-value">{pending.length}</div>
          <div className="stat-detail">Awaiting decision</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Processed</div>
          <div className="stat-value">{processed.length}</div>
          <div className="stat-detail">Today</div>
        </div>
      </div>

      {!loading && pending.length > 0 && (
        <div className="approvals-section">
          <h2>Pending Approvals</h2>
          <div className="approvals-list">
            {pending.map((approval) => (
              <div key={approval.id} className="approval-card">
                <div className="approval-header">
                  <div>
                    <h3>{approval.description}</h3>
                    <p className="approval-preview">{approval.preview}</p>
                  </div>
                  <span className={`type-badge type-${approval.type}`}>
                    {approval.type.toUpperCase()}
                  </span>
                </div>
                <div className="approval-actions">
                  <button
                    className="approval-btn approval-btn-approve"
                    onClick={() => handleApprove(approval.id)}
                    disabled={processing === approval.id}
                  >
                    ✓ Approve
                  </button>
                  <button
                    className="approval-btn approval-btn-deny"
                    onClick={() => handleDeny(approval.id)}
                    disabled={processing === approval.id}
                  >
                    ✗ Deny
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {processed.length > 0 && (
        <div className="approvals-section">
          <h2>Recently Processed</h2>
          <div className="approvals-list">
            {processed.map((approval) => (
              <div key={approval.id} className="approval-card processed">
                <div className="approval-header">
                  <div>
                    <h3>{approval.description}</h3>
                    <p className="approval-preview">{approval.preview}</p>
                  </div>
                  <span
                    className={`type-badge type-${approval.type} status-${approval.status}`}
                  >
                    {approval.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && approvals.length === 0 && (
        <div className="empty-state">
          <p>✓ No pending approvals</p>
          <p className="empty-hint">All caught up for now</p>
        </div>
      )}
    </div>
  );
};
