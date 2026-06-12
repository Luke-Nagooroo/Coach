import React from 'react';

function CVReview({ analysis, onContinue }) {
  const cleanItem = (value) => (value || '').replace(/\*\*/g, '').trim();
  const strongAreas = analysis?.strong_areas || analysis?.key_strengths || [];
  const improvementAreas = analysis?.improvement_areas || analysis?.improvements || [];
  const needsReworking = analysis?.needs_reworking || [];
  const suggestedFocus = analysis?.suggested_focus || [];
  const readinessScore = Number(analysis?.readiness_score ?? analysis?.score ?? 0);

  return (
    <div className="card interview-card">
      <div className="review-hero">
        <div className="review-hero__copy">
          <div className="eyebrow">CV Review</div>
          <h2>{analysis?.review_title || 'Here’s what stands out in your CV'}</h2>
          <p>{analysis?.summary || 'The CV has been reviewed and the strongest areas are highlighted below.'}</p>
        </div>

        <div className="review-score">
          <span>CV Readiness</span>
          <strong>{Number.isFinite(readinessScore) ? readinessScore : 0}</strong>
          <small>out of 100</small>
        </div>
      </div>

      <div className="feedback-box review-callout">
        <h3>Overall verdict</h3>
        <p>{analysis?.overall_assessment || 'Review complete'}</p>
      </div>

      <div className="feedback-panel">
        <div className="feedback-grid">
          <div className="feedback-card feedback-card--good">
            <h4>Strong Areas</h4>
            <ul>
              {strongAreas.length > 0 ? (
                strongAreas.map((item, index) => <li key={`strong-${index}`}>{item}</li>)
              ) : (
                <li>No strong areas were extracted.</li>
              )}
            </ul>
          </div>

          <div className="feedback-card feedback-card--improve">
            <h4>Areas to Improve</h4>
            <ul>
              {improvementAreas.length > 0 ? (
                improvementAreas.map((item, index) => <li key={`improve-${index}`}>{cleanItem(item)}</li>)
              ) : (
                <li>No improvement areas were extracted.</li>
              )}
            </ul>
          </div>

          <div className="feedback-card">
            <h4>Needs Reworking</h4>
            <ul>
              {needsReworking.length > 0 ? (
                needsReworking.map((item, index) => <li key={`rewrite-${index}`}>{item}</li>)
              ) : (
                <li>Nothing major needs to be rewritten right now.</li>
              )}
            </ul>
          </div>
        </div>

        <div className="feedback-suggestion">
          <h4>Priority Focus</h4>
          <p>
            {suggestedFocus.length > 0
              ? suggestedFocus.join(' ')
              : 'Tailor the CV to the role, tighten the wording, and make the impact clearer.'}
          </p>
        </div>
      </div>

      <div className="action-row review-actions">
        <button className="primary-button" onClick={onContinue}>
          Continue to Role Selection
        </button>
      </div>
    </div>
  );
}

export default CVReview;
