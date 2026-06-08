import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Interview({ sessionId, role, onInterviewEnd, initialQuestion, initialQuestionNumber }) {
  const [question, setQuestion] = useState(initialQuestion || null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(initialQuestionNumber || 1);

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
    if (!answer.trim()) {
      alert('Please provide an answer');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/interview/submit-answer', {
        session_id: sessionId,
        answer: answer
      });

      setQuestion(response.data.next_question);
      setQuestionNumber(response.data.question_number);
      setAnswer('');
    } catch (err) {
      alert('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
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
          <p className="section-label">Current prompt</p>
          <p className="question-text">{question}</p>
        </div>

        <div className="answer-section">
          <label className="section-label" htmlFor="answer-box">Your answer</label>
          <textarea
            id="answer-box"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer here..."
            disabled={loading}
          />
          <div className="action-row">
            <button onClick={handleSubmitAnswer} disabled={loading} className="primary-button">
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
