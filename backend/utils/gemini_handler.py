import os
import json
import random
import tempfile

# If GEMINI_MOCK is set (1/true), use deterministic mock responses to avoid
# calling the external API during local testing. Otherwise use the real
# google.generativeai client when available.
API_KEY = os.getenv('GEMINI_API_KEY')
PROXY_VALUES = [
    os.getenv('HTTP_PROXY', ''),
    os.getenv('HTTPS_PROXY', ''),
    os.getenv('http_proxy', ''),
    os.getenv('https_proxy', ''),
]
HAS_BLOCKED_LOCAL_PROXY = any(
    '127.0.0.1:9' in value or 'localhost:9' in value
    for value in PROXY_VALUES
)
if HAS_BLOCKED_LOCAL_PROXY:
    for proxy_name in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
        proxy_value = os.getenv(proxy_name, '')
        if '127.0.0.1:9' in proxy_value or 'localhost:9' in proxy_value:
            os.environ.pop(proxy_name, None)

USE_MOCK = (
    os.getenv('GEMINI_MOCK', '0').lower() in ('1', 'true', 'yes')
    or not API_KEY
    or API_KEY == 'your_key_here'
)

if not USE_MOCK:
    try:
        import google.generativeai as genai
        # Configure Gemini API
        genai.configure(api_key=API_KEY)
    except Exception:
        # Fall back to mock mode if the library isn't installed or config fails
        USE_MOCK = True


class GeminiHandler:
    """Handles all interactions with Google Gemini API or returns mock data."""

    def __init__(self):
        self.local_transcription_model = None
        self.last_request_source = 'local' if USE_MOCK else 'gemini'
        if not USE_MOCK:
            # Default to a non-Pro/free model that is commonly available
            model_id = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
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

    def _generate_content_text(self, payload, fallback_text=''):
        try:
            response = self.model.generate_content(payload)
            self.last_request_source = 'gemini'
            return response.text
        except Exception as e:
            self.last_request_source = 'local'
            print(f'Gemini request failed, using fallback response: {e}')
            return fallback_text

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
        response_text = self._generate_content_text(prompt)
        return self._normalize_cv_review(response_text)

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

        response_text = self._generate_content_text([
            prompt,
            {
                'mime_type': mime_type,
                'data': image_bytes,
            },
        ])
        return self._normalize_cv_review(response_text)

    def generate_interview_question(self, role, cv_analysis, question_count=0):
        local_questions = {
            'software engineer': [
                'Tell me about a challenging software project you worked on and how you approached it.',
                'Describe a production bug that was difficult to diagnose. How did you find and fix it?',
                'Tell me about a technical decision where you had to balance delivery speed and code quality.',
                'Describe a time you improved the performance or reliability of an application.',
                'How have you handled a disagreement about a software design or implementation?',
                'Tell me about a system you designed to remain maintainable as its requirements grew.',
            ],
            'frontend engineer': [
                'Tell me about a difficult user-interface problem you solved.',
                'Describe a time you improved the performance of a frontend application.',
                'How have you made a complex interface accessible and responsive?',
                'Tell me about a frontend architecture decision and the trade-offs you considered.',
            ],
            'backend engineer': [
                'Describe an API or backend service you designed and the trade-offs you made.',
                'Tell me about a database performance problem you diagnosed and resolved.',
                'How have you designed a service to handle failures and remain reliable?',
                'Describe a time you improved the scalability of a backend system.',
            ],
            'data scientist': [
                'Tell me about a data project where the initial results were misleading.',
                'Describe how you validated a model before recommending its use.',
                'Tell me about a time poor data quality affected a project and how you handled it.',
                'How have you explained a complex analytical result to a non-technical stakeholder?',
            ],
            'devops engineer': [
                'Describe a deployment or infrastructure failure you investigated and resolved.',
                'Tell me about a process you automated and the impact it had.',
                'How have you improved observability for a production system?',
                'Describe how you balanced reliability, cost, and delivery speed in an infrastructure decision.',
            ],
            'machine learning engineer': [
                'Tell me about a machine-learning model you moved from experimentation into production.',
                'Describe a problem involving model drift or degraded prediction quality.',
                'How have you balanced inference performance and model accuracy?',
                'Tell me about a difficult data pipeline problem in a machine-learning system.',
            ],
        }
        role_key = (role or '').lower()
        question_pool = local_questions.get(role_key, local_questions['software engineer'])
        fallback_question = random.choice(question_pool)

        if USE_MOCK:
            self.last_request_source = 'local'
            return fallback_question

        prompt = f"""
        Generate a single interview question for a {role} position.
        This is question #{question_count + 1}.

        Based on this candidate's CV:
        {cv_analysis}

        Create a relevant, specific question that assesses their fit for this role.
        Keep it under 2 sentences. Make it progressively harder with each question number.
        """

        response_text = self._generate_content_text(
            prompt,
            fallback_text=fallback_question,
        )
        return response_text.strip()

    def _evaluate_answer_locally(self, answer):
        normalized_answer = ' '.join((answer or '').lower().split())
        words = normalized_answer.split()
        vague_phrases = (
            'this is my answer',
            'i do not know',
            "i don't know",
            'no answer',
            'test answer',
        )
        is_vague = any(phrase in normalized_answer for phrase in vague_phrases)
        has_example = any(word in normalized_answer for word in (
            'project', 'example', 'when', 'situation', 'task', 'challenge',
            'built', 'created', 'implemented', 'designed', 'managed',
        ))
        has_outcome = any(character.isdigit() for character in normalized_answer) or any(
            word in normalized_answer for word in (
                'result', 'improved', 'reduced', 'increased', 'saved',
                'delivered', 'outcome', 'impact',
            )
        )

        if is_vague or len(words) < 8:
            score = 1
        elif len(words) < 20:
            score = 3
        elif len(words) < 40:
            score = 5
        else:
            score = 6

        if has_example:
            score += 1
        if has_outcome:
            score += 1
        score = min(score, 10)

        strengths = []
        if has_example:
            strengths.append('Included a concrete example')
        if has_outcome:
            strengths.append('Described an outcome or impact')
        if len(words) >= 20:
            strengths.append('Provided enough detail to assess the response')

        improvements = []
        if len(words) < 20:
            improvements.append('Give a complete answer with context, actions, and results')
        if not has_example:
            improvements.append('Include a specific example from your experience')
        if not has_outcome:
            improvements.append('Explain the result and measurable impact')

        suggestion = (
            'Use a specific situation, explain what you did, and finish with the result.'
            if score < 6
            else 'Add sharper metrics and explain the trade-offs behind your decisions.'
        )
        return {
            'score': score,
            'strengths': strengths,
            'improvements': improvements,
            'suggestion': suggestion
        }

    def evaluate_answer(self, question, answer, role, cv_analysis):
        local_evaluation = self._evaluate_answer_locally(answer)
        if USE_MOCK:
            return local_evaluation

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

        response_text = self._generate_content_text(prompt)
        parsed = self._parse_json_response(
            response_text,
            fallback=local_evaluation,
        )

        # Normalize common field types for the frontend.
        parsed.setdefault('score', local_evaluation['score'])
        parsed.setdefault('strengths', local_evaluation['strengths'])
        parsed.setdefault('improvements', local_evaluation['improvements'])
        parsed.setdefault('suggestion', local_evaluation['suggestion'])
        return parsed

    def _transcribe_audio_locally(self, audio_bytes, suffix='.webm'):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return ''

        if self.local_transcription_model is None:
            model_size = os.getenv('WHISPER_MODEL', 'tiny.en')
            self.local_transcription_model = WhisperModel(
                model_size,
                device='cpu',
                compute_type='int8',
            )

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name

            segments, _ = self.local_transcription_model.transcribe(
                temp_path,
                language='en',
                vad_filter=True,
            )
            return ' '.join(segment.text.strip() for segment in segments).strip()
        except Exception as e:
            print(f'Local transcription failed: {e}')
            return ''
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def transcribe_audio(self, audio_bytes, mime_type='audio/webm'):
        if not audio_bytes:
            return ''

        suffix = '.webm' if 'webm' in mime_type else '.mp3'
        local_transcript = self._transcribe_audio_locally(audio_bytes, suffix)
        if local_transcript:
            return local_transcript

        if USE_MOCK:
            return ''

        prompt = """
        Transcribe this interview answer accurately.
        Return only the spoken words as plain text.
        Do not evaluate, summarize, or add commentary.
        """
        return self._generate_content_text([
            prompt,
            {
                'mime_type': mime_type,
                'data': audio_bytes,
            },
        ]).strip()

    def _generate_final_review_locally(self, role, answers):
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

        average_ten_point_score = total_score / len(evaluations) if evaluations else 0
        overall_score = round(average_ten_point_score * 10)
        weak_interview = overall_score < 50
        return {
            'title': 'More answer detail is needed' if weak_interview else 'Final interview review',
            'overall_score': overall_score,
            'summary': (
                f'You completed {len(answers)} question(s), but the answers were too brief or vague to demonstrate readiness for the {role} role.'
                if weak_interview
                else f'You completed {len(answers)} question(s) for the {role} role and provided enough detail for a useful review.'
            ),
            'strengths': (
                ['Completed the interview and submitted usable recordings']
                if weak_interview
                else ['Provided assessable answers', 'Used relevant examples', 'Completed the interview consistently']
            ),
            'improvements': [
                'Answer the question directly instead of using placeholder phrases',
                'Give a specific example with context and actions',
                'Explain the outcome and measurable impact',
            ],
            'next_steps': ['Practice concise STAR-style answers', 'Prepare 2-3 stronger examples with numbers', 'Align your CV and interview stories more closely'],
            'closing_note': (
                'A recording counts as an answer, but its content still needs enough detail to be evaluated well.'
                if weak_interview
                else 'A little more specificity and evidence will make the answers stronger.'
            ),
            'question_count': len(answers),
            'answers': answers,
        }

    def generate_final_review(self, role, cv_analysis, answers):
        local_review = self._generate_final_review_locally(role, answers)
        if USE_MOCK:
            return local_review

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

        Recorded voice answers are valid answers. Use their transcripts exactly
        like typed answers and never ask the candidate to provide text answers.

        Return only valid JSON, no additional text.
        """

        response_text = self._generate_content_text(prompt)
        parsed = self._parse_json_response(
            response_text,
            fallback=local_review,
        )

        try:
            parsed['overall_score'] = int(parsed.get('overall_score', parsed.get('score', local_review['overall_score'])) or 0)
        except Exception:
            parsed['overall_score'] = local_review['overall_score']

        parsed.setdefault('title', local_review['title'])
        parsed.setdefault('summary', local_review['summary'])
        parsed.setdefault('strengths', local_review['strengths'])
        parsed.setdefault('improvements', local_review['improvements'])
        parsed.setdefault('next_steps', local_review['next_steps'])
        parsed.setdefault('closing_note', local_review['closing_note'])
        parsed['question_count'] = len(answers)
        parsed['answers'] = answers
        return parsed


# Create a singleton instance
gemini = GeminiHandler()
