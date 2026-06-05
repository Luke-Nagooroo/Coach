import React, { useState } from 'react';
import axios from 'axios';

function RoleSelector({ userId, onRoleSelected }) {
  const roles = [
    'Software Engineer',
    'Data Scientist',
    'Frontend Engineer',
    'Backend Engineer',
    'DevOps Engineer',
    'Machine Learning Engineer'
  ];

  const [loading, setLoading] = useState(false);

  const handleRoleSelect = async (role) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/interview/start', {
        role: role,
        user_id: userId
      });
      // Pass initial question and question number through to the app
      onRoleSelected(
        role,
        response.data.session_id,
        response.data.question,
        response.data.question_number
      );
    } catch (err) {
      alert('Failed to start interview: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Step 2: Select Target Role</h2>
      <p>Which position are you preparing for?</p>
      <div className="role-grid">
        {roles.map((role) => (
          <button
            key={role}
            onClick={() => handleRoleSelect(role)}
            disabled={loading}
            className="role-button"
          >
            {role}
          </button>
        ))}
      </div>
    </div>
  );
}

export default RoleSelector;
