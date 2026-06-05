import os

# Load GEMINI_API_KEY from .env without printing
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('GEMINI_API_KEY='):
                key = line.split('=',1)[1].strip()
                os.environ['GEMINI_API_KEY'] = key
                break

# Ensure mock disabled
os.environ['GEMINI_MOCK'] = '0'

# Run a single test call
from utils.gemini_handler import gemini
try:
    q = gemini.generate_interview_question('backend', '', 0)
    print('OK_RESPONSE_START')
    print(q)
    print('OK_RESPONSE_END')
except Exception as e:
    print('ERROR_RESPONSE_START')
    print(str(e))
    print('ERROR_RESPONSE_END')
