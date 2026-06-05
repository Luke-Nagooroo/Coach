import React, { useState } from 'react';
import axios from 'axios';

function CVUpload({ userId, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);

    try {
      const response = await axios.post('/api/cv/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      onUploadSuccess(response.data.analysis);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Step 1: Upload Your CV</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          onChange={handleFileChange}
          accept=".txt,.pdf,.png,.jpg,.jpeg"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !file}>
          {loading ? 'Analyzing...' : 'Upload & Analyze CV'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default CVUpload;
