import os
import json

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
            model_id = os.getenv('GEMINI_MODEL', 'models/gemini-1.5-flash')
            self.model = genai.GenerativeModel(model_id)

    def _build_cv_review_prompt(self, cv_content, content_type='text'):
        source_label = 'CV image' if content_type == 'image' else 'CV'
        return f"""
        Review this {source_label} and return a JSON response with:
        - review_title: a short headline for the overall CV verdict
        - summary: a short overall summary of the candidate profile
        - readiness_score: an integer from 1 to 100 showing overall CV strength
        - strong_areas: list of the candidate's strongest areas
        - improvement_areas: list of areas that can be improved
        - needs_reworking: list of sections, gaps, or choices that should be changed entirely
        - suggested_focus: list of the highest priority next steps
        - overall_assessment: a short verdict on the CV's readiness

        {source_label} Content:
        {cv_content}

        Return only valid JSON, no additional text.
        """

    def _fallback_cv_review(self, raw_text=''):
        return {
            'review_title': 'Solid base, but it needs sharper positioning',
            'summary': 'A solid starting point, but the CV could be sharper and more targeted.',
            'readiness_score': 72,
            'strong_areas': ['Clear professional direction', 'Relevant experience', 'Useful skills shown'],
            'improvement_areas': ['Add measurable outcomes', 'Tighten bullet points', 'Make the profile more role-specific'],
            'needs_reworking': ['Any long generic responsibilities', 'Skills that are not tied to evidence'],
            'suggested_focus': ['Lead with the most relevant experience', 'Use metrics where possible', 'Remove anything that does not support the target role'],
            'overall_assessment': 'Good foundation, but it would benefit from a more focused rewrite for the role you want.',
            'raw_text': raw_text,
        }

    def _normalize_cv_review(self, response_text, fallback=None):
        parsed = self._parse_json_response(response_text, fallback=fallback or self._fallback_cv_review())
        if not isinstance(parsed, dict):
            parsed = self._fallback_cv_review(str(parsed))

        normalized = self._fallback_cv_review(parsed.get('raw_text', ''))
        normalized.update(parsed)
        try:
            normalized['readiness_score'] = int(normalized.get('readiness_score', normalized.get('score', 0)) or 0)
        except Exception:
            normalized['readiness_score'] = 0
        normalized.setdefault('summary', normalized['summary'])
        normalized.setdefault('review_title', normalized['review_title'])
        normalized.setdefault('strong_areas', [])
        normalized.setdefault('improvement_areas', [])
        normalized.setdefault('needs_reworking', [])
        normalized.setdefault('suggested_focus', [])
        normalized.setdefault('overall_assessment', '')
        return normalized

    def analyze_cv(self, cv_text):
        if USE_MOCK:
            skill_hits = []
            lower_text = cv_text.lower()
            if 'python' in lower_text:
                skill_hits.append('Python')
            if 'react' in lower_text:
                skill_hits.append('React')
            if 'django' in lower_text or 'flask' in lower_text:
                skill_hits.append('Web development')

            return {
                'review_title': 'Good foundation with clear technical signals',
                'summary': 'This CV shows a practical background with room to sharpen impact and focus.',
                'readiness_score': 76,
                'strong_areas': skill_hits or ['Communication', 'Problem solving'],
                'improvement_areas': ['Add metrics to achievements', 'Tighten wording', 'Clarify role progression'],
                'needs_reworking': ['Any generic bullets that do not show outcomes'],
                'suggested_focus': ['Lead with relevant experience', 'Quantify impact', 'Tailor the CV to the target role'],
                'overall_assessment': 'Promising, but it would benefit from a more targeted rewrite.',
            }

        prompt = self._build_cv_review_prompt(cv_text, content_type='text')
        response = self.model.generate_content(prompt)
        return self._normalize_cv_review(response.text)

    def _parse_json_response(self, response_text, fallback=None):
        fallback = fallback or {}
        if isinstance(response_text, dict):
            return response_text

        text = (response_text or '').strip()
        if not text:
            return fallback

        # Strip code fences if the model wrapped the JSON.
        if text.startswith('```'):
            lines = text.splitlines()
            if len(lines) >= 3:
                text = '\n'.join(lines[1:-1]).strip()

        try:
            return json.loads(text)
        except Exception:
            return {
                **fallback,
                'raw_text': text,
            }

    def analyze_cv_image(self, image_bytes, mime_type='image/png'):
        if USE_MOCK:
            return {
                'review_title': 'Readable and structured, but it can be sharper',
                'summary': 'The CV image is readable and appears well structured.',
                'readiness_score': 74,
                'strong_areas': ['Clear layout', 'Relevant experience', 'Readable formatting'],
                'improvement_areas': ['Add more measurable impact', 'Reduce generic phrasing'],
                'needs_reworking': ['Any dense sections that are hard to scan quickly'],
                'suggested_focus': ['Make the top third more specific', 'Add evidence for key claims'],
                'overall_assessment': 'A decent CV image, but the content could be sharpened for stronger impact.',
            }

        prompt = self._build_cv_review_prompt('[image content supplied to Gemini]', content_type='image')

        response = self.model.generate_content([
            prompt,
            {
                'mime_type': mime_type,
                'data': image_bytes,
            },
        ])
        return self._normalize_cv_review(response.text)

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
        parsed = self._parse_json_response(
            response.text,
            fallback={
                'score': 0,
                'strengths': [],
                'improvements': [],
                'suggestion': 'No structured feedback returned by Gemini.',
            },
        )

        # Normalize common field types for the frontend.
        parsed.setdefault('score', 0)
        parsed.setdefault('strengths', [])
        parsed.setdefault('improvements', [])
        parsed.setdefault('suggestion', '')
        return parsed

    def generate_final_review(self, role, cv_analysis, answers):
        if USE_MOCK:
            total_score = 0
            evaluations = []
            for item in answers:
                evaluation = item.get('evaluation') or {}
                score = evaluation.get('score', 0) or 0
                try:
                    total_score += int(score)
                except Exception:
                    pass
                if evaluation:
                    evaluations.append(evaluation)

            average_score = round(total_score / len(evaluations)) if evaluations else 0
            return {
                'title': 'Final interview review',
                'overall_score': average_score,
                'summary': f'You completed {len(answers)} question(s) for the {role} role and showed a solid base to build on.',
                'strengths': ['Kept answers structured', 'Showed role awareness', 'Handled multiple prompts with consistency'],
                'improvements': ['Add more measurable impact', 'Be more specific with examples', 'Tie answers more directly to business outcomes'],
                'next_steps': ['Practice concise STAR-style answers', 'Prepare 2-3 stronger examples with numbers', 'Align your CV and interview stories more closely'],
                'closing_note': 'You are close, but a little more specificity and evidence will make a big difference.',
                'question_count': len(answers),
                'answers': answers,
            }

        prompt = f"""
        Review this completed interview for a {role} role and return a JSON response with:
        - title: a short headline for the final review
        - overall_score: an integer from 1 to 100
        - summary: a short summary of the interview performance
        - strengths: list of the strongest points from the interview
        - improvements: list of the biggest opportunities to improve
        - next_steps: list of practical next steps before the next interview
        - closing_note: one short sentence ending the review

        CV analysis:
        {cv_analysis}

        Interview answers and evaluations:
        {answers}

        Return only valid JSON, no additional text.
        """

        response = self.model.generate_content(prompt)
        parsed = self._parse_json_response(
            response.text,
            fallback={
                'title': 'Final interview review',
                'overall_score': 0,
                'summary': 'The interview is complete, but Gemini did not return a structured final review.',
                'strengths': [],
                'improvements': [],
                'next_steps': [],
                'closing_note': 'Use the answer-level feedback to refine your next run.',
            },
        )

        try:
            parsed['overall_score'] = int(parsed.get('overall_score', parsed.get('score', 0)) or 0)
        except Exception:
            parsed['overall_score'] = 0

        parsed.setdefault('title', 'Final interview review')
        parsed.setdefault('summary', '')
        parsed.setdefault('strengths', [])
        parsed.setdefault('improvements', [])
        parsed.setdefault('next_steps', [])
        parsed.setdefault('closing_note', '')
        parsed['question_count'] = len(answers)
        parsed['answers'] = answers
        return parsed


# Create a singleton instance
gemini = GeminiHandler()
