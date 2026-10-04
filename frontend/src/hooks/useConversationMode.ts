import { useState, useCallback, useRef } from 'react';
import { startRecording, stopRecordingAndTranscribe, setRecordingStateCallback } from '@/services/stt';
import { speak } from '@/services/tts';

export type ConversationState = 'idle' | 'listening' | 'thinking' | 'speaking';

const EXIT_PHRASES = ['that\'s all', 'goodbye', 'stop listening', 'exit', 'quit', 'bye'];
const NO_SPEECH_TIMEOUT = 30000; // 30 seconds
const TTS_RESUME_DELAY = 300; // 300ms after TTS ends

interface UseConversationModeOptions {
  conversationId: string;
  onStateChange?: (state: ConversationState) => void;
  onVolumeChange?: (level: number) => void;
  onTranscript?: (text: string) => void;
  onResponse?: (response: string) => void;
  onError?: (error: string) => void;
}

export function useConversationMode(options: UseConversationModeOptions) {
  const [isActive, setIsActive] = useState(false);
  const [state, setState] = useState<ConversationState>('idle');
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');

  const isSpeakingRef = useRef(false);
  const noSpeechTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const isListeningRef = useRef(false);

  const updateState = useCallback((newState: ConversationState) => {
    setState(newState);
    options.onStateChange?.(newState);
  }, [options]);

  const updateError = useCallback((err: string) => {
    setError(err);
    options.onError?.(err);
  }, [options]);

  const handleExit = useCallback(async () => {
    setIsActive(false);
    updateState('idle');
    setTranscript('');
    setResponse('');
    setError('');
  }, [updateState]);

  const checkExitPhrase = (text: string): boolean => {
    const lower = text.toLowerCase();
    return EXIT_PHRASES.some(phrase => lower.includes(phrase));
  };

  const processWithAgent = useCallback(
    async (question: string): Promise<{ answer: string; shouldContinue: boolean }> => {
      try {
        updateState('thinking');
        setTranscript(question);
        options.onTranscript?.(question);

        const res = await fetch('/api/agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            conversation_id: options.conversationId,
          }),
        });

        if (!res.ok) {
          throw new Error(`Agent error: ${res.statusText}`);
        }

        const data = await res.json();
        const answer = data.response || '';

        setResponse(answer);
        options.onResponse?.(answer);

        // Check if user wants to exit
        if (checkExitPhrase(question)) {
          updateState('idle');
          await handleExit();
          return { answer, shouldContinue: false };
        }

        return { answer, shouldContinue: true };
      } catch (err) {
        updateError(err instanceof Error ? err.message : 'Agent error');
        return { answer: '', shouldContinue: false };
      }
    },
    [options, updateState, updateError, handleExit]
  );

  const speakResponse = useCallback(
    async (text: string) => {
      if (!text) return;

      try {
        isSpeakingRef.current = true;
        updateState('speaking');

        await speak(text);

        isSpeakingRef.current = false;

        // Resume listening after delay
        setTimeout(() => {
          if (isActive && !isListeningRef.current) {
            startListeningLoop();
          }
        }, TTS_RESUME_DELAY);
      } catch (err) {
        isSpeakingRef.current = false;
        console.log('TTS not available, continuing to next turn');
        // Continue conversation even if TTS fails
        setTimeout(() => {
          if (isActive) {
            startListeningLoop();
          }
        }, TTS_RESUME_DELAY);
      }
    },
    [isActive, updateState]
  );

  const startListeningLoop = useCallback(async () => {
    if (!isActive || isSpeakingRef.current) return;

    try {
      isListeningRef.current = true;
      updateState('listening');
      setVolumeLevel(0);

      // Set up volume monitoring
      setRecordingStateCallback((state) => {
        setVolumeLevel(state.rmsLevel);
        options.onVolumeChange?.(state.rmsLevel);
      });

      await startRecording();

      // Set no-speech timeout
      if (noSpeechTimeoutRef.current) {
        clearTimeout(noSpeechTimeoutRef.current);
      }
      noSpeechTimeoutRef.current = setTimeout(() => {
        if (isListeningRef.current) {
          stopListeningLoop();
        }
      }, NO_SPEECH_TIMEOUT);
    } catch (err) {
      updateError(err instanceof Error ? err.message : 'Microphone error');
      isListeningRef.current = false;
    }
  }, [isActive, updateState, updateError, options]);

  const stopListeningLoop = useCallback(async () => {
    if (noSpeechTimeoutRef.current) {
      clearTimeout(noSpeechTimeoutRef.current);
    }

    if (!isListeningRef.current) return;

    try {
      isListeningRef.current = false;
      const question = await stopRecordingAndTranscribe();

      // Process with agent
      const { answer, shouldContinue } = await processWithAgent(question);

      if (shouldContinue && isActive) {
        // Speak response and loop
        await speakResponse(answer);
      }
    } catch (err) {
      if (err instanceof Error && err.message === 'No speech detected') {
        // No speech detected, just loop again
        if (isActive) {
          startListeningLoop();
        }
      } else {
        updateError(err instanceof Error ? err.message : 'Processing error');
      }
    }
  }, [isActive, processWithAgent, speakResponse, updateError, startListeningLoop]);

  const start = useCallback(async () => {
    setIsActive(true);
    updateState('listening');
    await startListeningLoop();
  }, [updateState, startListeningLoop]);

  const stop = useCallback(async () => {
    if (noSpeechTimeoutRef.current) {
      clearTimeout(noSpeechTimeoutRef.current);
    }
    if (isListeningRef.current) {
      try {
        await stopRecordingAndTranscribe();
      } catch {
        // Ignore stop errors
      }
    }
    await handleExit();
  }, [handleExit]);

  return {
    isActive,
    state,
    volumeLevel,
    transcript,
    response,
    error,
    start,
    stop,
    stopListeningLoop,
  };
}
