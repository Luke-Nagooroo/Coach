import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VoiceRecorder from './VoiceRecorder';

function Interview({ sessionId, role, onInterviewEnd, initialQuestion, initialQuestionNumber, initialQuestionSource }) {
  const [question, setQuestion] = useState(initialQuestion || null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(initialQuestionNumber || 1);
  const [questionSource, setQuestionSource] = useState(initialQuestionSource || 'local');
  const [audioFilename, setAudioFilename] = useState(null);
  const [audioTranscript, setAudioTranscript] = useState('');

  useEffect(() => {
    // If an initial question was not provided, fetch the session's current question
    if (!question && sessionId) {
      // Could add an endpoint to fetch session details; for now we rely on start response
    }
    // Update question number if prop changes
    setQuestionNumber(initialQuestionNumber || questionNumber);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion, initialQuestionNumber]);

  const handleSubmitAnswer = async () => {
    if (!answer.trim() && !audioFilename) {
      alert('Please type an answer or upload a recording');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/interview/submit-answer', {
        session_id: sessionId,
        answer: answer.trim(),
        audio_file: audioFilename || null,
        transcript: audioTranscript,
      });

      setQuestion(response.data.next_question);
      setQuestionNumber(response.data.question_number);
      setQuestionSource(response.data.question_source || 'local');
      setAnswer('');
      setAudioFilename(null);
      setAudioTranscript('');
    } catch (err) {
      alert('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAudioUploaded = (filename, transcript) => {
    setAudioFilename(filename);
    setAudioTranscript(transcript || '');
  };

  const handleEndInterview = async () => {
    try {
      const response = await axios.post('/api/interview/end-interview', {
        session_id: sessionId
      });

      onInterviewEnd(response.data.final_review || null, response.data);
    } catch (err) {
      alert('Error ending interview: ' + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div className="card interview-card">
      <div className="section-header">
        <div>
          <p className="eyebrow">Step 3</p>
          <h2>Interview for {role}</h2>
        </div>
        <div className="question-pill">Question {questionNumber}</div>
      </div>

      <div className="interview-container">
        <div className="question-section">
          <div className="question-meta">
            <p className="section-label">Current prompt</p>
            <span className={`question-source question-source--${questionSource}`}>
              {questionSource === 'gemini' ? 'Gemini question' : 'Local fallback'}
            </span>
          </div>
          <p className="question-text">{question}</p>
        </div>

        <div className="answer-section">
          <VoiceRecorder
            key={questionNumber}
            onUploaded={handleAudioUploaded}
          />
          {audioFilename && (
            <p className="upload-success">
              Recording uploaded and ready as your answer.
            </p>
          )}
          <label className="section-label" htmlFor="answer-box">Your answer</label>
          <textarea
            id="answer-box"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type an answer, or upload a recording above..."
            disabled={loading}
          />
          <div className="action-row">
            <button
              onClick={handleSubmitAnswer}
              disabled={loading || (!answer.trim() && !audioFilename)}
              className="primary-button"
            >
              {loading ? 'Processing...' : 'Submit Answer'}
            </button>
            {questionNumber > 1 && (
              <button
                onClick={handleEndInterview}
                className="end-button secondary-button"
              >
                End Interview
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Interview;
