import React from 'react';
import './VoiceFeedback.css';

interface VoiceFeedbackProps {
  isRecording: boolean;
  transcript: string;
  isProcessing: boolean;
  error?: string;
}

export const VoiceFeedback = ({
  isRecording,
  transcript,
  isProcessing,
  error,
}: VoiceFeedbackProps) => {
  return (
    <div className="voice-feedback">
      {isRecording && (
        <div className="recording-indicator">
          <div className="mic-pulse">
            <span className="mic-dot"></span>
          </div>
          <span className="recording-text">Recording...</span>
        </div>
      )}

      {transcript && (
        <div className="transcript-box">
          <div className="transcript-label">You said:</div>
          <div className="transcript-text">"{transcript}"</div>
          {!isProcessing && (
            <div className="transcript-hint">Sending to agent...</div>
          )}
        </div>
      )}

      {isProcessing && (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <span className="processing-text">Agent is thinking...</span>
        </div>
      )}

      {error && (
        <div className="error-box">
          <span className="error-icon">⚠</span>
          <span className="error-text">{error}</span>
        </div>
      )}
    </div>
  );
};
