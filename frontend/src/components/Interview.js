import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Interview({ sessionId, role, onInterviewEnd, initialQuestion, initialQuestionNumber }) {
  const [question, setQuestion] = useState(initialQuestion || null);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(initialQuestionNumber || 1);
  const [evaluation, setEvaluation] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

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

      setEvaluation(response.data.evaluation);
      setQuestion(response.data.next_question);
      setQuestionNumber(response.data.question_number);
      setAnswer('');
      setShowFeedback(true);

      // Hide feedback after 3 seconds, then show next question
      setTimeout(() => {
        setShowFeedback(false);
      }, 3000);
    } catch (err) {
      alert('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Step 3: Interview - {role}</h2>
      <div className="interview-container">
        <div className="question-section">
          <p className="question-number">Question {questionNumber}</p>
          <p className="question-text">{question}</p>
        </div>

        {showFeedback && evaluation && (
          <div className="feedback-box">
            <h4>Feedback</h4>
            <p>{evaluation}</p>
          </div>
        )}

        {!showFeedback && (
          <div className="answer-section">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here..."
              disabled={loading}
            />
            <button onClick={handleSubmitAnswer} disabled={loading}>
              {loading ? 'Processing...' : 'Submit Answer'}
            </button>
            {questionNumber > 1 && (
              <button
                onClick={() => {
                  axios.post('/api/interview/end-interview', { session_id: sessionId });
                  onInterviewEnd();
                }}
                className="end-button"
              >
                End Interview
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Interview;
