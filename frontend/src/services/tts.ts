const API_BASE = '/api';

interface TTSOptions {
  voiceId?: string;
  model?: string;
  speed?: number;
}

/**
 * Text-to-speech via ElevenLabs (backend proxy)
 * Backend should expose POST /api/tts that handles ElevenLabs auth
 */
export async function textToSpeech(
  text: string,
  options: TTSOptions = {}
): Promise<AudioBuffer> {
  const res = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      voice_id: options.voiceId,
      model: options.model || 'eleven_monolingual_v1',
      speed: options.speed || 1.0,
    }),
  });

  if (!res.ok) {
    throw new Error(`TTS failed: ${res.statusText}`);
  }

  const audioBuffer = await res.arrayBuffer();
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  return audioContext.decodeAudioData(audioBuffer);
}

/**
 * Play audio through Web Audio API
 */
export async function playAudio(audioBuffer: AudioBuffer): Promise<void> {
  return new Promise((resolve, reject) => {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;

    source.connect(audioContext.destination);

    source.onended = () => resolve();
    source.addEventListener('error', reject);

    source.start(0);
  });
}

/**
 * Text-to-speech and play in one call
 */
export async function speak(text: string, options: TTSOptions = {}): Promise<void> {
  const audioBuffer = await textToSpeech(text, options);
  await playAudio(audioBuffer);
}
