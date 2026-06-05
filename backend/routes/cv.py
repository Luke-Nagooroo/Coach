from flask import Blueprint, request, jsonify
from utils.gemini_handler import gemini
import json

# Create a blueprint (modular route group)
cv_bp = Blueprint('cv', __name__)

# Store CV data in memory (in production, use a database)
cv_storage = {}

@cv_bp.route('/upload', methods=['POST'])
def upload_cv():
    """
    Endpoint to upload and analyze CV
    Expects: multipart form-data with 'file' field
    Returns: CV analysis result
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Read file content and handle PDFs/images
    content = file.read()
    cv_text = None

    filename = (file.filename or '').lower()
    content_type = (file.content_type or '').lower()

    # Image files (jpg, jpeg, png) -> send directly to Gemini vision
    if filename.endswith(('.png', '.jpg', '.jpeg')) or content_type.startswith('image/'):
        try:
            image_mime = content_type if content_type.startswith('image/') else (
                'image/jpeg' if filename.endswith(('.jpg', '.jpeg')) else 'image/png'
            )
            analysis = gemini.analyze_cv_image(content, image_mime)

            user_id = request.form.get('user_id', 'default')
            cv_storage[user_id] = {
                'raw_text': '[image uploaded]',
                'analysis': analysis
            }

            return jsonify({
                'success': True,
                'analysis': analysis,
                'user_id': user_id
            })
        except Exception as e:
            return jsonify({'error': f'Failed to analyze image CV: {str(e)}'}), 500

    # If PDF, attempt to extract text using PyPDF2
    elif filename.endswith('.pdf') or content_type == 'application/pdf' or 'pdf' in filename:
        try:
            from PyPDF2 import PdfReader
            import io

            reader = PdfReader(io.BytesIO(content))
            texts = []
            for page in reader.pages:
                page_text = page.extract_text() or ''
                texts.append(page_text)
            cv_text = '\n'.join(texts).strip()
        except Exception as e:
            cv_text = ''

        if not cv_text:
            return jsonify({'error': 'PDF appears to be image-based or empty. Please upload a text-based PDF or convert the PDF pages to images and upload those instead.'}), 400

    else:
        try:
            cv_text = content.decode('utf-8')
        except Exception:
            return jsonify({'error': 'Could not read file. Please use a text file, a text-based PDF, or an image (PNG/JPG).'}), 400

    try:
        # Analyze CV with Gemini
        analysis = gemini.analyze_cv(cv_text)

        # Store CV data for later use
        user_id = request.form.get('user_id', 'default')
        cv_storage[user_id] = {
            'raw_text': cv_text,
            'analysis': analysis
        }

        return jsonify({
            'success': True,
            'analysis': analysis,
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({'error': f'Failed to analyze CV: {str(e)}'}), 500

@cv_bp.route('/get/<user_id>', methods=['GET'])
def get_cv_analysis(user_id):
    """Retrieve stored CV analysis for a user"""
    if user_id in cv_storage:
        return jsonify(cv_storage[user_id])
    return jsonify({'error': 'CV not found'}), 404
