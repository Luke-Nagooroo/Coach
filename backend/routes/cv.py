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

    # Image files (jpg, jpeg, png) -> OCR with pytesseract
    if filename.endswith(('.png', '.jpg', '.jpeg')) or content_type.startswith('image/'):
        try:
            from PIL import Image
            import pytesseract
            import io

            img = Image.open(io.BytesIO(content))
            cv_text = pytesseract.image_to_string(img)
            cv_text = cv_text.strip()
            if not cv_text:
                return jsonify({'error': 'Could not extract text from the image. Try a clearer image or a text-based PDF.'}), 400
        except Exception as e:
            return jsonify({'error': f'OCR error: {str(e)}. Ensure Pillow and pytesseract are installed and Tesseract is available on PATH.'}), 500

    # If PDF, attempt to extract text using PyPDF2, else OCR via pdf2image+pytesseract if available
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
            # Try OCR fallback using pdf2image + pytesseract if available
            try:
                from pdf2image import convert_from_bytes
                from PIL import Image
                import pytesseract
                images = convert_from_bytes(content)
                texts = []
                for img in images:
                    page_text = pytesseract.image_to_string(img) or ''
                    texts.append(page_text)
                cv_text = '\n'.join(texts).strip()
                if not cv_text:
                    return jsonify({'error': 'Could not extract text from PDF (it may be scanned or image-only).'}), 400
            except Exception as e:
                # Couldn't OCR; prompt user to provide a text-based PDF or install OCR dependencies
                return jsonify({'error': 'PDF appears to be image-based and OCR fallback is not available. To enable OCR for PDFs, install `pdf2image` and system `poppler`, plus `pytesseract` and Tesseract OCR.'}), 400

    else:
        try:
            cv_text = content.decode('utf-8')
        except Exception:
            return jsonify({'error': 'Could not read file. Please use a text file, a text-based PDF, or an image (PNG/JPG) for OCR.'}), 400

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
