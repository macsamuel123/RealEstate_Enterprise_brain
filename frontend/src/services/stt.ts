let currentRecorder: MediaRecorder | null = null;
let currentStream: MediaStream | null = null;

export async function startRecording(): Promise<void> {
  try {
    currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    currentRecorder = new MediaRecorder(currentStream);
    currentRecorder.start();
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

    currentRecorder!.ondataavailable = (e) => chunks.push(e.data);

    currentRecorder!.onstop = async () => {
      currentStream!.getTracks().forEach((track) => track.stop());
      currentRecorder = null;
      currentStream = null;

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
      currentStream?.getTracks().forEach((track) => track.stop());
      currentRecorder = null;
      currentStream = null;
      reject(new Error(`Recording error: ${event.error}`));
    };

    currentRecorder!.stop();
  });
}

export async function recordAndTranscribe(): Promise<string> {
  await startRecording();
  return new Promise((resolve) => {
    setTimeout(() => {
      stopRecordingAndTranscribe().then(resolve);
    }, 3000); // Auto-stop after 3 seconds for testing
  });
}
