import { useState, useEffect } from 'react';
import { Ring } from '@/components/Ring';
import { VoiceFeedback } from '@/components/VoiceFeedback';
import { RingState, Brief, BusinessMetrics } from '@/types';
import { getBriefs, getMetrics } from '@/services/api';
import { speak } from '@/services/tts';
import { recordAndTranscribe } from '@/services/stt';
import './Home.css';

export const Home = () => {
  const [ringState, setRingState] = useState<RingState>('idle');
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [metrics, setMetrics] = useState<BusinessMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastQuestion, setLastQuestion] = useState<string>('');
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [conversationId, setConversationId] = useState<string>('');
  const [pendingApproval, setPendingApproval] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [briefsData, metricsData] = await Promise.all([getBriefs(), getMetrics()]);
        setBriefs(briefsData);
        setMetrics(metricsData);
      } catch (err) {
        console.error('Failed to load home data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleRingClick = async () => {
    if (ringState === 'idle') {
      // Start listening
      setRingState('listening');
      setError('');
      setPendingApproval(null);

      try {
        const question = await recordAndTranscribe();
        setLastQuestion(question);

        // Send to agent for processing
        setRingState('speaking');
        await handleQuestion(question);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error during processing');
        setRingState('idle');
      }
    } else if (ringState === 'speaking') {
      // Stop speaking
      setRingState('idle');
    }
  };

  const handleQuestion = async (question: string) => {
    setTranscript(question);
    try {
      // Call backend agent endpoint with the question
      const res = await fetch('/api/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          conversation_id: conversationId
        }),
      });

      if (!res.ok) {
        throw new Error(`Agent error: ${res.statusText}`);
      }

      const data = await res.json();
      const answer = data.response || data.answer;

      // Store conversation ID from first response
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Check for pending approval
      if (data.pending_approval) {
        setPendingApproval(data.pending_approval);
        console.log('Pending approval:', data.pending_approval);
      }

      // Speak the answer (will fail without ElevenLabs key, but shows response text)
      try {
        await speak(answer);
      } catch (ttsErr) {
        console.log('TTS not available, but got response:', answer);
      }
    } catch (err) {
      console.error('Agent error:', err);
      setError(err instanceof Error ? err.message : 'Failed to get answer');
    } finally {
      setRingState('idle');
    }
  };

  const handleApproveAction = async (approvalId: string) => {
    try {
      setRingState('speaking');
      const res = await fetch(`/api/approvals/${approvalId}/approve`, {
        method: 'POST',
      });

      if (!res.ok) {
        throw new Error('Failed to approve action');
      }

      const data = await res.json();
      setPendingApproval(null);
      console.log('Action approved:', data);

      try {
        await speak('Action approved and executed');
      } catch (ttsErr) {
        console.log('TTS failed, but action was approved');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve action');
    } finally {
      setRingState('idle');
    }
  };

  const handleDenyAction = async (approvalId: string) => {
    try {
      setRingState('speaking');
      const res = await fetch(`/api/approvals/${approvalId}/deny`, {
        method: 'POST',
      });

      if (!res.ok) {
        throw new Error('Failed to deny action');
      }

      setPendingApproval(null);

      try {
        await speak('Action cancelled');
      } catch (ttsErr) {
        console.log('TTS failed, but action was cancelled');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deny action');
    } finally {
      setRingState('idle');
    }
  };

  return (
    <div className="home">
      <div className="home-header">
        <h1>AI Chief of Staff</h1>
        <p className="subtitle">Getty Group • Calgary, AB</p>
      </div>

      <div className="home-main">
        <div className="ring-section">
          <Ring state={ringState} onClick={handleRingClick} />
          <p className="ring-hint">
            {ringState === 'idle' && 'Click ring to ask a question'}
            {ringState === 'listening' && 'Listening... speak your question'}
            {ringState === 'speaking' && 'Agent is responding...'}
          </p>
        </div>

        <VoiceFeedback
          isRecording={ringState === 'listening'}
          transcript={transcript || lastQuestion}
          isProcessing={ringState === 'speaking'}
          error={error}
        />

        {pendingApproval && (
          <div className="approval-card">
            <div className="approval-header">
              <h3>Action Requires Approval</h3>
            </div>
            <div className="approval-details">
              <p><strong>Action:</strong> {pendingApproval.action}</p>
              <p><strong>To:</strong> {pendingApproval.to}</p>
              <p><strong>Subject:</strong> {pendingApproval.subject}</p>
              <div className="approval-body">
                <p><strong>Message:</strong></p>
                <p>{pendingApproval.body}</p>
              </div>
            </div>
            <div className="approval-actions">
              <button
                onClick={() => handleApproveAction(pendingApproval.approval_id)}
                className="btn-approve"
              >
                Approve
              </button>
              <button
                onClick={() => handleDenyAction(pendingApproval.approval_id)}
                className="btn-deny"
              >
                Deny
              </button>
            </div>
          </div>
        )}

        {!loading && metrics && (
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">{metrics.leadsToday}</div>
              <div className="metric-label">New Leads</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.activeDeal}</div>
              <div className="metric-label">Active Deals</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.approvalsPending}</div>
              <div className="metric-label">Pending</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.agentsActive}</div>
              <div className="metric-label">Active</div>
            </div>
          </div>
        )}
      </div>

      {briefs.length > 0 && (
        <div className="briefs-section">
          <h2>Morning Briefs</h2>
          <div className="briefs-list">
            {briefs.map((brief) => (
              <div key={brief.id} className={`brief-card priority-${brief.priority}`}>
                <div className="brief-header">
                  <h3>{brief.title}</h3>
                  <span className="brief-time">
                    {formatTime(brief.timestamp)}
                  </span>
                </div>
                <p className="brief-content">{brief.content}</p>
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
