import React from 'react';

function FinalReview({ review, summary, onRestart }) {
  const cleanItem = (value) => (value || '').replace(/\*\*/g, '').trim();
  const strengths = review?.strengths || [];
  const improvements = review?.improvements || [];
  const nextSteps = review?.next_steps || [];

  return (
    <div className="card interview-card">
      <div className="review-hero">
        <div className="review-hero__copy">
          <div className="eyebrow">Final Review</div>
          <h2>{review?.title || 'Interview complete'}</h2>
          <p>{review?.summary || 'Your interview has been reviewed and summarized below.'}</p>
        </div>

        <div className="review-score">
          <span>Overall</span>
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

      <div className="action-row review-actions">
        <button className="primary-button" onClick={onRestart}>
          Start New Interview
        </button>
      </div>
    </div>
  );
}

export default FinalReview;