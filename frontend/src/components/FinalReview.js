import React, { useState } from 'react';

function FinalReview({ review, summary, onRestart }) {
  const [showAnswers, setShowAnswers] = useState(false);
  const cleanItem = (value) => (value || '').replace(/\*\*/g, '').trim();
  const strengths = review?.strengths || [];
  const improvements = review?.improvements || [];
  const nextSteps = review?.next_steps || [];
  const answers = summary?.answers || review?.answers || [];

  return (
    <div className="card interview-card">
      <div className="review-hero">
        <div className="review-hero__copy">
          <div className="eyebrow">Final Review</div>
          <h2>{review?.title || 'Interview complete'}</h2>
          <p>{review?.summary || 'Your interview has been reviewed and summarized below.'}</p>
        </div>

        <div className="review-score">
          <span>Interview Score</span>
          <strong>{Number(review?.overall_score ?? 0) || 0}</strong>
          <small>out of 100</small>
        </div>
      </div>

      <div className="feedback-box review-callout">
        <h3>Closing note</h3>
        <p>{review?.closing_note || 'Keep refining your answers with more specifics and measurable outcomes.'}</p>
        {summary?.total_questions !== undefined && (
          <p style={{ marginTop: '0.65rem' }}>
            Completed {summary.total_questions} question{summary.total_questions === 1 ? '' : 's'}.
          </p>
        )}
      </div>

      <div className="feedback-grid">
        <div className="feedback-card feedback-card--good">
          <h4>Strengths</h4>
          <ul>
            {strengths.length > 0 ? strengths.map((item, index) => <li key={`final-strength-${index}`}>{item}</li>) : <li>No strengths captured.</li>}
          </ul>
        </div>

        <div className="feedback-card feedback-card--improve">
          <h4>Improvements</h4>
          <ul>
            {improvements.length > 0 ? improvements.map((item, index) => <li key={`final-improve-${index}`}>{cleanItem(item)}</li>) : <li>No improvements captured.</li>}
          </ul>
        </div>

        <div className="feedback-card">
          <h4>Next Steps</h4>
          <ul>
            {nextSteps.length > 0 ? nextSteps.map((item, index) => <li key={`final-next-${index}`}>{item}</li>) : <li>Keep practising with sharper examples.</li>}
          </ul>
        </div>
      </div>

      {answers.length > 0 && (
        <div className="answer-review">
          <button
            type="button"
            className="secondary-button"
            onClick={() => setShowAnswers((current) => !current)}
            aria-expanded={showAnswers}
          >
            {showAnswers ? 'Hide Answer Review' : 'Review Answers'}
          </button>

          {showAnswers && (
            <div className="answer-review__list">
              {answers.map((item, index) => {
                const transcript = cleanItem(item.transcript || item.answer);
                const score = item.evaluation?.score;

                return (
                  <section className="answer-review__item" key={`answer-review-${index}`}>
                    <div className="answer-review__heading">
                      <span>Question {index + 1}</span>
                      {score !== undefined && score !== null && (
                        <strong>{score}/10</strong>
                      )}
                    </div>
                    <h3>{item.question}</h3>
                    <p className="answer-review__label">Recording transcript</p>
                    <p className="answer-review__transcript">
                      {transcript || 'No transcript was captured for this recording.'}
                    </p>
                    {item.audio_file && (
                      <audio
                        controls
                        preload="metadata"
                        src={`/api/interview/audio/${encodeURIComponent(item.audio_file)}`}
                      />
                    )}
                  </section>
                );
              })}
            </div>
          )}
        </div>
      )}

      <div className="action-row review-actions">
        <button className="primary-button" onClick={onRestart}>
          Start New Interview
        </button>
      </div>
    </div>
  );
}

export default FinalReview;
