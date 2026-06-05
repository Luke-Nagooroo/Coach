from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS - allows React frontend to communicate with this Flask backend
CORS(app)

# Import routes
from routes.cv import cv_bp
from routes.interview import interview_bp

# Register blueprints (modular route groups)
app.register_blueprint(cv_bp, url_prefix='/api/cv')
app.register_blueprint(interview_bp, url_prefix='/api/interview')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple endpoint to verify backend is running"""
    return jsonify({'status': 'ok', 'message': 'AI Coach backend is running'})

if __name__ == '__main__':
    # Debug=True allows auto-reload and better error messages during development
    # Allow overriding port via PORT env var for flexible testing
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
