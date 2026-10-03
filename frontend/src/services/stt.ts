/**
 * Speech-to-text via Whisper (backend proxy)
 */
export async function recordAndTranscribe(): Promise<string> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  const chunks: BlobPart[] = [];

  mediaRecorder.ondataavailable = (e) => chunks.push(e.data);

  mediaRecorder.start();

  // Record for up to 30 seconds or until user stops
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      mediaRecorder.stop();
    }, 30000);

    mediaRecorder.onstop = async () => {
      clearTimeout(timeout);
      stream.getTracks().forEach((track) => track.stop());

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
        resolve(data.text);
      } catch (error) {
        reject(error);
      }
    };

    mediaRecorder.onerror = reject;
  });
}
