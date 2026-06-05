import React, { useState } from 'react';
import CVUpload from './components/CVUpload';
import RoleSelector from './components/RoleSelector';
import Interview from './components/Interview';
import './App.css';

function App() {
  const [stage, setStage] = useState('upload'); // 'upload', 'role-select', 'interview', 'feedback'
  const [userId, setUserId] = useState(`user_${Date.now()}`);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [initialQuestion, setInitialQuestion] = useState(null);
  const [initialQuestionNumber, setInitialQuestionNumber] = useState(1);

  const handleCVUploaded = (analysis) => {
    setCvAnalysis(analysis);
    setStage('role-select');
  };

  const handleRoleSelected = (role, sessionId, question, questionNumber) => {
    setSelectedRole(role);
    setSessionId(sessionId);
    setInitialQuestion(question || null);
    setInitialQuestionNumber(questionNumber || 1);
    setStage('interview');
  };

  const handleInterviewEnd = () => {
    setStage('feedback');
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎓 AI Interview Coach</h1>
      </header>

      <main className="container">
        {stage === 'upload' && (
          <CVUpload userId={userId} onUploadSuccess={handleCVUploaded} />
        )}

        {stage === 'role-select' && (
          <RoleSelector userId={userId} onRoleSelected={handleRoleSelected} />
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
          <div className="feedback-section">
            <h2>Interview Complete! 🎉</h2>
            <p>Check back soon for detailed feedback.</p>
            <button onClick={() => window.location.reload()}>Start New Interview</button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
