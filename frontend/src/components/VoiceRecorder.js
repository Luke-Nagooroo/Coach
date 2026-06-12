import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

function VoiceRecorder({ onUploaded }) {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [captureWarning, setCaptureWarning] = useState('');
  const [uploaded, setUploaded] = useState(false);
  const [transcript, setTranscript] = useState('');
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);
  const audioContextRef = useRef(null);
  const levelFrameRef = useRef(null);
  const maxLevelRef = useRef(0);
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef('');

  const loadAudioDevices = async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    const devices = await navigator.mediaDevices.enumerateDevices();
    const inputs = devices.filter((device) => device.kind === 'audioinput');
    setAudioDevices(inputs);
    setSelectedDeviceId((current) => (
      current && inputs.some((device) => device.deviceId === current)
        ? current
        : inputs[0]?.deviceId || ''
    ));
  };

  useEffect(() => {
    loadAudioDevices().catch(() => {});
    return () => {
      if (levelFrameRef.current) cancelAnimationFrame(levelFrameRef.current);
      audioContextRef.current?.close().catch(() => {});
      streamRef.current?.getTracks().forEach((track) => track.stop());
      recognitionRef.current?.stop();
    };
  }, []);

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  const stopLevelMonitor = () => {
    if (levelFrameRef.current) {
      cancelAnimationFrame(levelFrameRef.current);
      levelFrameRef.current = null;
    }
    audioContextRef.current?.close().catch(() => {});
    audioContextRef.current = null;
    setAudioLevel(0);
  };

  const startLevelMonitor = (stream) => {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;

    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    const samples = new Uint8Array(analyser.fftSize);
    source.connect(analyser);
    audioContextRef.current = context;

    const updateLevel = () => {
      analyser.getByteTimeDomainData(samples);
      let sumSquares = 0;
      for (const sample of samples) {
        const normalized = (sample - 128) / 128;
        sumSquares += normalized * normalized;
      }
      const level = Math.min(1, Math.sqrt(sumSquares / samples.length) * 4);
      maxLevelRef.current = Math.max(maxLevelRef.current, level);
      setAudioLevel(level);
      levelFrameRef.current = requestAnimationFrame(updateLevel);
    };

    updateLevel();
  };

  const startTranscription = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    finalTranscriptRef.current = '';

    recognition.onresult = (event) => {
      let interimTranscript = '';
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const text = event.results[index][0].transcript;
        if (event.results[index].isFinal) {
          finalTranscriptRef.current += `${text} `;
        } else {
          interimTranscript += text;
        }
      }
      setTranscript(`${finalTranscriptRef.current}${interimTranscript}`.trim());
    };

    recognition.onerror = (event) => {
      if (!['aborted', 'no-speech'].includes(event.error)) {
        setCaptureWarning('The recording worked, but automatic transcription was unavailable.');
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopTranscription = () => {
    const recognition = recognitionRef.current;
    if (recognition) {
      recognition.stop();
      recognitionRef.current = null;
    }
  };

  const startRecording = async () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(null);
    setAudioBlob(null);
    setCaptureWarning('');
    setUploaded(false);
    setTranscript('');
    finalTranscriptRef.current = '';
    maxLevelRef.current = 0;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          ...(selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : {}),
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;
      await loadAudioDevices();
      startLevelMonitor(stream);
      startTranscription();
      const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? { mimeType: 'audio/webm;codecs=opus' }
        : {};
      const mr = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const mimeType = mr.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: mimeType });
        stopLevelMonitor();
        stopStream();
        if (blob.size === 0) {
          alert('No audio was captured. Please check your microphone and try again.');
          return;
        }
        if (maxLevelRef.current < 0.02) {
          setCaptureWarning('No microphone signal was detected. Select another input and record again.');
        }
        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);
      };

      mr.start(250);
      setRecording(true);
    } catch (err) {
      stopTranscription();
      stopLevelMonitor();
      stopStream();
      alert('Unable to access microphone: ' + err.message);
    }
  };

  const stopRecording = () => {
    stopTranscription();
    const mr = mediaRecorderRef.current;
    if (mr && mr.state === 'recording') {
      mr.requestData();
      mr.stop();
    } else {
      stopStream();
    }
    setRecording(false);
  };

  const upload = async () => {
    if (!audioBlob) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append('audio', audioBlob, 'recording.webm');

      const resp = await axios.post('/api/interview/upload-audio', form);

      if (resp.data?.success) {
        const uploadedTranscript = (resp.data.transcript || transcript).trim();
        setTranscript(uploadedTranscript);
        if (!uploadedTranscript) {
          setCaptureWarning('The recording uploaded, but no speech could be transcribed. Try speaking closer to the microphone.');
        }
        setUploaded(true);
        onUploaded?.(resp.data.filename, uploadedTranscript);
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
      {audioDevices.length > 0 && (
        <label className="recorder-device">
          Microphone
          <select
            value={selectedDeviceId}
            onChange={(event) => setSelectedDeviceId(event.target.value)}
            disabled={recording}
          >
            {audioDevices.map((device, index) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `Microphone ${index + 1}`}
              </option>
            ))}
          </select>
        </label>
      )}

      <div className="recorder-controls">
        {!recording && <button onClick={startRecording} className="primary-button">Start Recording</button>}
        {recording && <button onClick={stopRecording} className="end-button">Stop</button>}
      </div>

      {recording && (
        <div className="audio-level" aria-label="Microphone input level">
          <span style={{ width: `${Math.max(3, audioLevel * 100)}%` }} />
        </div>
      )}

      {captureWarning && <p className="error">{captureWarning}</p>}

      {audioUrl && (
        <div className="recorder-playback">
          <audio
            ref={audioRef}
            controls
            preload="metadata"
            src={audioUrl}
            onLoadedMetadata={() => {
              audioRef.current.muted = false;
              audioRef.current.volume = 1;
            }}
          />
          {transcript && (
            <p className="voice-transcript">
              <strong>Captured answer:</strong> {transcript}
            </p>
          )}
          <div style={{ marginTop: '0.5rem' }}>
            <button onClick={upload} disabled={uploading || uploaded} className="primary-button">
              {uploading ? 'Uploading & Transcribing...' : uploaded ? 'Recording Uploaded' : 'Upload Recording'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default VoiceRecorder;
