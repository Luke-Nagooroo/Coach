import os

# If GEMINI_MOCK is set (1/true), use deterministic mock responses to avoid
# calling the external API during local testing. Otherwise use the real
# google.generativeai client when available.
USE_MOCK = os.getenv('GEMINI_MOCK', '0').lower() in ('1', 'true', 'yes')

if not USE_MOCK:
    try:
        import google.generativeai as genai
        # Configure Gemini API
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    except Exception:
        # Fall back to mock mode if the library isn't installed or config fails
        USE_MOCK = True


class GeminiHandler:
    """Handles all interactions with Google Gemini API or returns mock data."""

    def __init__(self):
        if not USE_MOCK:
            # Default to a non-Pro/free model that is commonly available
            model_id = os.getenv('GEMINI_MODEL', 'models/gemini-flash-latest')
            self.model = genai.GenerativeModel(model_id)

    def analyze_cv(self, cv_text):
        if USE_MOCK:
            # Very simple heuristic/mock parse
            skills = []
            if 'Python' in cv_text:
                skills.append('Python')
            if 'React' in cv_text:
                skills.append('React')
            if 'Django' in cv_text or 'Flask' in cv_text:
                skills.append('Web')
            return {
                'skills': skills or ['Communication'],
                'experience': ['Example Corp - Software Engineer'],
                'years_of_experience': 3,
                'key_strengths': ['Problem solving', 'Teamwork', 'Learning']
            }

        prompt = f"""
        Analyze this CV and provide a JSON response with:
        - skills: list of technical skills
        - experience: list of past roles and companies
        - years_of_experience: total years
        - key_strengths: top 3 strengths based on CV

        CV Content:
        {cv_text}

        Return only valid JSON, no additional text.
        """

        response = self.model.generate_content(prompt)
        return response.text

    def generate_interview_question(self, role, cv_analysis, question_count=0):
        if USE_MOCK:
            # Return a deterministic question based on role and count
            base = {
                'backend': 'Explain how you would design a REST API for high throughput.',
                'frontend': 'How would you optimize rendering in a large React app?',
                'default': f'Tell me about a challenging project you worked on related to {role}.'
            }
            q = base.get(role.lower(), base['default'])
            if question_count > 0:
                q += f' (follow-up #{question_count})'
            return q

        prompt = f"""
        Generate a single interview question for a {role} position.
        This is question #{question_count + 1}.

        Based on this candidate's CV:
        {cv_analysis}

        Create a relevant, specific question that assesses their fit for this role.
        Keep it under 2 sentences. Make it progressively harder with each question number.
        """

        response = self.model.generate_content(prompt)
        return response.text.strip()

    def evaluate_answer(self, question, answer, role, cv_analysis):
        if USE_MOCK:
            # Very simple mock evaluation
            score = 7
            strengths = ['Clear structure', 'Relevant examples']
            improvements = ['Add metrics', 'Discuss trade-offs']
            suggestion = 'Briefly mention measurable outcomes and trade-offs.'
            return {
                'score': score,
                'strengths': strengths,
                'improvements': improvements,
                'suggestion': suggestion
            }

        prompt = f"""
        Evaluate this interview answer on a scale of 1-10.
        Role: {role}
        Question: {question}
        Answer: {answer}

        Candidate's background: {cv_analysis}

        Return a JSON response with:
        - score: integer from 1-10
        - strengths: list of what they did well
        - improvements: list of areas to improve
        - suggestion: one sentence on how to improve

        Return only valid JSON, no additional text.
        """

        response = self.model.generate_content(prompt)
        return response.text


# Create a singleton instance
gemini = GeminiHandler()
