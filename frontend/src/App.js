import React, { useState } from 'react';
import CVUpload from './components/CVUpload';
import RoleSelector from './components/RoleSelector';
import Interview from './components/Interview';
import CVReview from './components/CVReview';
import FinalReview from './components/FinalReview';
import './App.css';

function App() {
  const [stage, setStage] = useState('upload'); // 'upload', 'cv-review', 'role-select', 'interview', 'feedback'
  const [userId] = useState(`user_${Date.now()}`);
  const [selectedRole, setSelectedRole] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [initialQuestion, setInitialQuestion] = useState(null);
  const [initialQuestionNumber, setInitialQuestionNumber] = useState(1);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [finalReview, setFinalReview] = useState(null);
  const [interviewSummary, setInterviewSummary] = useState(null);

  const handleCVUploaded = (analysis) => {
    setCvAnalysis(analysis);
    setStage('cv-review');
  };

  const handleContinueFromReview = () => {
    setStage('role-select');
  };

  const handleRoleSelected = (role, sessionId, question, questionNumber) => {
    setSelectedRole(role);
    setSessionId(sessionId);
    setInitialQuestion(question || null);
    setInitialQuestionNumber(questionNumber || 1);
    setStage('interview');
  };

  const handleInterviewEnd = (review, summary) => {
    setFinalReview(review);
    setInterviewSummary(summary);
    setStage('feedback');
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎓 AI Interview Coach</h1>
        <p>Upload a CV, pick a role, and practice with structured Gemini feedback that highlights strengths, gaps, and next steps.</p>
      </header>

      <main className="container">
        {stage === 'upload' && (
          <CVUpload userId={userId} onUploadSuccess={handleCVUploaded} />
        )}

        {stage === 'cv-review' && (
          <CVReview analysis={cvAnalysis} onContinue={handleContinueFromReview} />
        )}

        {stage === 'role-select' && (
          <RoleSelector userId={userId} cvAnalysis={cvAnalysis} onRoleSelected={handleRoleSelected} />
        )}

        {stage === 'interview' && (
          <Interview
            sessionId={sessionId}
            role={selectedRole}
            initialQuestion={initialQuestion}
            initialQuestionNumber={initialQuestionNumber}
            onInterviewEnd={handleInterviewEnd}
          />
        )}

        {stage === 'feedback' && (
          <FinalReview
            review={finalReview}
            summary={interviewSummary}
            onRestart={() => window.location.reload()}
          />
        )}
      </main>
    </div>
  );
}

export default App;
