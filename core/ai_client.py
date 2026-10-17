import json
import os
import re
import requests
from .integrations import integration_value


def _extract_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI did not return JSON")
    return json.loads(text[start:end + 1])


def generate_quest(topic, source, difficulty="mixed", levels=3):
    prompt = f'''Create a rigorous learning quest in English. Topic: {topic}. Difficulty: {difficulty}. Context: {source[:9000]}. Return ONLY JSON with keys title, description, levels. levels must contain exactly {levels} objects. Each level has title, summary, questions. Each level has 4 multiple choice questions, each with prompt, options (exactly 4 concise strings), correct_index (0-3), explanation. Questions must be factual and grounded in context when provided. No markdown.'''
    errors = []
    gemini_key = integration_value("GEMINI_API_KEY")
    if gemini_key:
        try:
            model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
            response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": gemini_key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.45, "thinkingConfig": {"thinkingLevel": "minimal"}, "maxOutputTokens": 8192, "responseMimeType": "application/json"}}, timeout=60)
            response.raise_for_status()
            parts = response.json()["candidates"][0]["content"]["parts"]
            value = _extract_json("\n".join(part.get("text", "") for part in parts if not part.get("thought")))
            return validate(value, levels), "gemma"
        except Exception as exc:
            errors.append(f"Gemma: {type(exc).__name__}")
    groq_key = integration_value("GROQ_API_KEY")
    if groq_key:
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}"}, json={"model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.5, "response_format": {"type": "json_object"}}, timeout=45)
            response.raise_for_status()
            value = _extract_json(response.json()["choices"][0]["message"]["content"])
            return validate(value, levels), "groq"
        except Exception as exc:
            errors.append(f"Groq: {type(exc).__name__}")
    raise ValueError("Quest generation is unavailable. Check the AI keys and model access. " + ", ".join(errors))


def validate(value, count):
    if not isinstance(value, dict) or not isinstance(value.get("levels"), list) or len(value["levels"]) != count:
        raise ValueError("AI returned an incomplete quest")
    for level in value["levels"]:
        if not isinstance(level.get("questions"), list) or len(level["questions"]) < 3:
            raise ValueError("AI returned incomplete questions")
        for question in level["questions"]:
            if not isinstance(question.get("options"), list) or len(question["options"]) != 4 or not isinstance(question.get("correct_index"), int) or question["correct_index"] not in range(4):
                raise ValueError("AI returned an invalid question")
    return value


def explain_answer(question):
    prompt = f"Explain this multiple-choice answer clearly in 2-3 sentences for a learner. Question: {question.prompt}. Options: {question.options}. Correct answer: {question.options[question.correct_index]}. Existing explanation: {question.explanation}"
    key = integration_value("GEMINI_API_KEY")
    if key:
        try:
            model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
            response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"thinkingConfig": {"thinkingLevel": "minimal"}, "maxOutputTokens": 400}}, timeout=30)
            response.raise_for_status()
            text = " ".join(part.get("text", "") for part in response.json()["candidates"][0]["content"]["parts"] if not part.get("thought")).strip()
            if text:
                return text
        except Exception:
            pass
    return question.explanation or "Review the correct option and try again."
