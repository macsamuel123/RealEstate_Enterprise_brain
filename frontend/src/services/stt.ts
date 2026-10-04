/**
 * Speech-to-text via Whisper with Voice Activity Detection (VAD)
 */

// VAD configuration (tunable for demo room)
export const VAD_CONFIG = {
  RMS_THRESHOLD: 0.02,           // RMS threshold for speech detection
  SILENCE_DURATION_MS: 1500,     // Duration of silence to trigger stop
  NO_SPEECH_TIMEOUT_MS: 6000,    // Cancel if no speech detected for 6s
  HARD_STOP_MS: 30000,           // Hard stop after 30s
  ANALYSIS_INTERVAL_MS: 50,      // RMS analysis frequency
};

let currentRecorder: MediaRecorder | null = null;
let currentStream: MediaStream | null = null;
let audioContext: AudioContext | null = null;
let analyser: AnalyserNode | null = null;

export interface RecordingState {
  rmsLevel: number;
  isSpeaking: boolean;
  hasSpeechDetected: boolean;
}

let recordingStateCallback: ((state: RecordingState) => void) | null = null;

export function setRecordingStateCallback(callback: (state: RecordingState) => void) {
  recordingStateCallback = callback;
}

function calculateRMS(dataArray: Uint8Array): number {
  let sum = 0;
  for (let i = 0; i < dataArray.length; i++) {
    const normalized = (dataArray[i] - 128) / 128;
    sum += normalized * normalized;
  }
  return Math.sqrt(sum / dataArray.length);
}

export async function startRecording(
  onVolumeChange?: (rms: number) => void
): Promise<void> {
  try {
    currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    currentRecorder = new MediaRecorder(currentStream);

    // Set up Web Audio for VAD
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;

    const source = audioContext.createMediaStreamSource(currentStream);
    source.connect(analyser);

    currentRecorder.start();

    // Start VAD monitoring
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const analysisInterval = setInterval(() => {
      if (!analyser) {
        clearInterval(analysisInterval);
        return;
      }

      analyser.getByteFrequencyData(dataArray);
      const rms = calculateRMS(dataArray);

      if (onVolumeChange) {
        onVolumeChange(rms);
      }

      if (recordingStateCallback) {
        recordingStateCallback({
          rmsLevel: rms,
          isSpeaking: rms > VAD_CONFIG.RMS_THRESHOLD,
          hasSpeechDetected: false,
        });
      }
    }, VAD_CONFIG.ANALYSIS_INTERVAL_MS);

    // Store interval ID for cleanup
    (currentRecorder as any).__analysisInterval = analysisInterval;
  } catch (error) {
    throw new Error(`Microphone access denied: ${error}`);
  }
}

export async function stopRecordingAndTranscribe(): Promise<string> {
  if (!currentRecorder || !currentStream) {
    throw new Error('No recording in progress');
  }

  return new Promise((resolve, reject) => {
    const chunks: BlobPart[] = [];
    let hasSpeech = false;

    currentRecorder!.ondataavailable = (e) => chunks.push(e.data);

    currentRecorder!.onstop = async () => {
      // Clean up
      const interval = (currentRecorder as any).__analysisInterval;
      if (interval) clearInterval(interval);

      currentStream!.getTracks().forEach((track) => track.stop());
      if (audioContext) audioContext.close();

      currentRecorder = null;
      currentStream = null;
      audioContext = null;
      analyser = null;

      // If no speech was detected, don't send to API
      if (!hasSpeech) {
        reject(new Error('No speech detected'));
        return;
      }

      const blob = new Blob(chunks, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', blob, 'audio.webm');

      try {
        const res = await fetch('/api/transcribe', {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`STT failed: ${res.statusText}`);
        }

        const data = await res.json();
        resolve(data.text || '');
      } catch (error) {
        reject(error);
      }
    };

    currentRecorder!.onerror = (event) => {
      const interval = (currentRecorder as any).__analysisInterval;
      if (interval) clearInterval(interval);

      currentStream?.getTracks().forEach((track) => track.stop());
      if (audioContext) audioContext.close();

      currentRecorder = null;
      currentStream = null;
      audioContext = null;
      analyser = null;

      reject(new Error(`Recording error: ${(event as any).error}`));
    };

    // Monitor for silence and no-speech timeout
    if (!analyser || !currentRecorder) {
      if (currentRecorder) {
        currentRecorder.stop();
      }
      return;
    }

    let lastSpeechTime = Date.now();
    let silenceStartTime: number | null = null;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const silenceCheckInterval = setInterval(() => {
      if (!analyser) {
        clearInterval(silenceCheckInterval);
        return;
      }

      analyser.getByteFrequencyData(dataArray);
      const rms = calculateRMS(dataArray);
      const isSpeaking = rms > VAD_CONFIG.RMS_THRESHOLD;

      if (isSpeaking) {
        hasSpeech = true;
        lastSpeechTime = Date.now();
        silenceStartTime = null;
      } else if (hasSpeech) {
        // Speech has started but now silent
        if (silenceStartTime === null) {
          silenceStartTime = Date.now();
        }

        const silenceDuration = Date.now() - silenceStartTime;
        if (silenceDuration > VAD_CONFIG.SILENCE_DURATION_MS) {
          clearInterval(silenceCheckInterval);
          currentRecorder!.stop();
        }
      }

      // No speech for 6 seconds: cancel
      if (!hasSpeech && Date.now() - lastSpeechTime > VAD_CONFIG.NO_SPEECH_TIMEOUT_MS) {
        clearInterval(silenceCheckInterval);
        currentRecorder!.stop();
      }
    }, VAD_CONFIG.ANALYSIS_INTERVAL_MS);

    // Hard stop after 30 seconds
    setTimeout(() => {
      clearInterval(silenceCheckInterval);
      if (currentRecorder) {
        currentRecorder.stop();
      }
    }, VAD_CONFIG.HARD_STOP_MS);
  });
}

export async function recordAndTranscribe(): Promise<string> {
  await startRecording();
  return stopRecordingAndTranscribe();
}
