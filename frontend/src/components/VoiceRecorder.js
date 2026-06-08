import React, { useState, useRef } from 'react';
import axios from 'axios';

function VoiceRecorder({ onUploaded }) {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    setAudioUrl(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
      };

      mr.start();
      setRecording(true);
    } catch (err) {
      alert('Unable to access microphone: ' + err.message);
    }
  };

  const stopRecording = () => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') mr.stop();
    setRecording(false);
  };

  const upload = async () => {
    if (!audioUrl) return;
    setUploading(true);
    try {
      const blob = await fetch(audioUrl).then(r => r.blob());
      const form = new FormData();
      form.append('audio', blob, 'recording.webm');

      const resp = await axios.post('/api/interview/upload-audio', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (resp.data?.success) {
        onUploaded?.(resp.data.filename);
      } else {
        alert('Upload failed');
      }
    } catch (err) {
      alert('Upload error: ' + (err.response?.data?.error || err.message));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="voice-recorder">
      <div className="recorder-controls">
        {!recording && <button onClick={startRecording} className="primary-button">Start Recording</button>}
        {recording && <button onClick={stopRecording} className="end-button">Stop</button>}
      </div>

      {audioUrl && (
        <div className="recorder-playback">
          <audio controls src={audioUrl} />
          <div style={{ marginTop: '0.5rem' }}>
            <button onClick={upload} disabled={uploading} className="primary-button">
              {uploading ? 'Uploading...' : 'Upload Recording'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;
