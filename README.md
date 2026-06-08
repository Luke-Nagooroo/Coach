# AI Interview Coach

Prepare for tech interviews with AI-powered practice sessions.

## Project Structure

```
ai-coach/
├── backend/              # Python Flask API
│   ├── app.py           # Main Flask app
│   ├── requirements.txt  # Python dependencies
│   ├── .env            # API keys (not in repo)
│   ├── routes/         # API endpoints
│   └── utils/          # Helper functions (Gemini integration)
├── frontend/            # React web app
│   ├── package.json
│   ├── src/
│   │   ├── App.js
│   │   ├── components/ # React components
│   │   └── index.js
│   └── public/
└── README.md
```

## Setup

### 1. Get Gemini API Key
- Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
- Create a new API key
- Copy it

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Update `.env`:
```
GEMINI_API_KEY=your_key_here
```

Run backend:
```bash
python app.py
```

Backend runs on `http://localhost:5000`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

## How It Works

1. **Upload CV** → AI analyzes your background
2. **Select Role** → Choose target position
3. **Interview** → AI asks questions based on role
4. **Feedback** → AI evaluates your answers

## API Endpoints

- `POST /api/cv/upload` - Upload and analyze CV
- `POST /api/interview/start` - Start interview session
- `POST /api/interview/submit-answer` - Submit answer, get feedback
- `POST /api/interview/end-interview` - End session

## Next Steps

- Add database to persist data
- Improve CV analysis
- Add more roles
- Add progress tracking
