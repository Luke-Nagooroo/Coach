from flask import Blueprint, request, jsonify
from utils.gemini_handler import gemini
import json
import os
import uuid
from flask import send_from_directory

interview_bp = Blueprint('interview', __name__)

# Store interview sessions in memory
sessions = {}
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@interview_bp.route('/start', methods=['POST'])
def start_interview():
    """
    Start a new interview session
    Expects: JSON with 'role' and 'user_id'
    Returns: First interview question
    """
    data = request.json
    role = data.get('role')
    user_id = data.get('user_id', 'default')
    cv_analysis = data.get('cv_analysis', 'No CV analysis yet')

    if not role:
        return jsonify({'error': 'Role is required'}), 400

    # Create a new session
    session_id = f"{user_id}_{role}"
    sessions[session_id] = {
        'role': role,
        'user_id': user_id,
        'cv_analysis': cv_analysis,
        'questions_asked': 0,
        'answers': []
    }

    try:
        # Generate first question
        question = gemini.generate_interview_question(role, cv_analysis, 0)
        sessions[session_id]['current_question'] = question

        return jsonify({
            'success': True,
            'session_id': session_id,
            'question': question,
            'question_number': 1
        })
    except Exception as e:
        return jsonify({'error': f'Failed to generate question: {str(e)}'}), 500

@interview_bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    """
    Submit an answer to the current question
    Expects: JSON with 'session_id', 'answer'
    Returns: Score, feedback, and next question
    """
    data = request.json
    session_id = data.get('session_id')
    answer = data.get('answer')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = sessions[session_id]

    try:
        # Evaluate the answer
        current_question = session.get('current_question')
        evaluation = gemini.evaluate_answer(
            current_question,
            answer,
            session['role'],
            session.get('cv_analysis', 'CV analysis would go here')
        )

        # Store answer
        # Include optional audio filename if provided in the request
        audio_file = request.json.get('audio_file') if request.is_json else None
        session['answers'].append({
            'question': current_question,
            'answer': answer,
            'audio_file': audio_file,
            'evaluation': evaluation
        })

        # Generate next question
        session['questions_asked'] += 1
        next_question = gemini.generate_interview_question(
            session['role'],
            session.get('cv_analysis', 'CV analysis'),
            session['questions_asked']
        )
        session['current_question'] = next_question

        return jsonify({
            'success': True,
            'evaluation': evaluation,
            'next_question': next_question,
            'question_number': session['questions_asked'] + 1
        })
    except Exception as e:
        return jsonify({'error': f'Failed to process answer: {str(e)}'}), 500

@interview_bp.route('/end-interview', methods=['POST'])
def end_interview():
    """End interview and get summary"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = sessions[session_id]

    final_review = gemini.generate_final_review(
        session['role'],
        session.get('cv_analysis', 'CV analysis would go here'),
        session['answers'],
    )

    # Return all answers and evaluations
    return jsonify({
        'success': True,
        'total_questions': len(session['answers']),
        'answers': session['answers'],
        'final_review': final_review
    })


@interview_bp.route('/upload-audio', methods=['POST'])
def upload_audio():
    """Accept audio file uploads (multipart/form-data with 'audio'). Returns a filename key."""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    f = request.files['audio']
    if f.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    ext = os.path.splitext(f.filename)[1] or '.webm'
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)

    return jsonify({'success': True, 'filename': filename})


@interview_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    # Security: only serve files from UPLOAD_DIR
    return send_from_directory(UPLOAD_DIR, filename)
