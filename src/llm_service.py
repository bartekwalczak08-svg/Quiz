import json
import os
from typing import Optional
import httpx
from dotenv import load_dotenv

from src.models import Question, Evaluation

load_dotenv()

class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY nie ustawiony. "
                "Ustaw zmienną środowiskową lub przekaż api_key."
            )
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model or "openai/gpt-5-mini"
        self.timeout = timeout

    def _parse_json_response(self, content: str, response_model):
        """Wyciąga JSON z odpowiedzi i parsuje do modelu Pydantic. Przy błędzie loguje całą odpowiedź i czyści typowe śmieci."""
        import re
        if content is None:
            raise ValueError("Model nie zwrócił odpowiedzi (content is None)")

        # Spróbuj znaleźć pierwszy poprawny JSON w odpowiedzi
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx == -1 or end_idx <= start_idx:
            # Spróbuj wyciągnąć JSON przez regex (bardziej odporne na śmieci)
            matches = re.findall(r'\{.*?\}', content, re.DOTALL)
            if matches:
                json_str = matches[0]
            else:
                raise ValueError(f"Nie znaleziono poprawnego JSON. Surowa odpowiedź modelu:\n{content}")
        else:
            json_str = content[start_idx:end_idx]

        # Usuń typowe śmieci (np. Odpowiedź modelu:, Odpowiedź:, itp.)
        json_str = re.sub(r'^[^{]*', '', json_str)
        json_str = re.sub(r'[^}]*$', '', json_str)

        # Loguj wyciągnięty fragment JSON
        print("[DEBUG] Wyciągnięty JSON do parsowania:")
        print(json_str)

        # Automatyczna naprawa typowych błędów
        # 1. Niedomknięte cudzysłowy na końcu
        if json_str.count('"') % 2 != 0:
            json_str = json_str.rstrip('"')
        # 2. Ucięty tekst po ostatniej klamrze
        last_brace = json_str.rfind('}')
        if last_brace != -1:
            json_str = json_str[:last_brace+1]

        try:
            data = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Błąd parsowania JSON: {e}\nWyciągnięty fragment:\n{json_str}\nSurowa odpowiedź modelu:\n{content}")

        obj = response_model(**data)
        # Walidacja score jeśli model to Evaluation
        if response_model.__name__ == "Evaluation":
            score = getattr(obj, "score", None)
            if not (isinstance(score, (int, float)) and 0 <= score <= 10):
                raise ValueError(f"score poza zakresem 0-10: {score}\n\nOdpowiedź modelu:\n" + str(content))
        return obj
        return obj

    def generate_question(self, topic: str, difficulty: str) -> Question:
        """Generuje pytanie quizowe za pośrednictwem OpenRouter.ai"""
        # Walidacja topic i difficulty
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("Topic nie może być pusty i musi być typu str")
        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty musi być jedną z: easy, medium, hard")

        prompt = f"""Wygeneruj pytanie quizowe w formacie JSON.

Temat: {topic}
Poziom trudności: {difficulty}

Zwróć odpowiedź WYŁĄCZNIE w tym formacie JSON (bez dodatkowego tekstu):
{{
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "question_text": "pytanie tutaj",
    "hint": "podpowiedź tutaj"
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/ai-quiz-master",
            "X-Title": "AI Quiz Master"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Jesteś nauczycielem programowania. Generujesz pytania quizowe w formacie JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return self._parse_json_response(content, Question)

    def evaluate_answer(self, question: str, user_answer: str) -> Evaluation:
        """Ocenia odpowiedź użytkownika za pośrednictwem OpenRouter.ai"""
        # Walidacja wejść
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question nie może być pusty i musi być typu str")
        if not isinstance(user_answer, str) or not user_answer.strip():
            raise ValueError("user_answer nie może być pusty i musi być typu str")

        prompt = f"""Oceń odpowiedź ucznia. Zwróć odpowiedź w formacie JSON.

Pytanie: {question}
Odpowiedź ucznia: {user_answer}

Zwróć odpowiedź WYŁĄCZNIE w tym formacie JSON (bez dodatkowego tekstu):
{{
    "is_correct": true lub false,
    "score": liczba od 0 do 10,
    "explanation": "wyjaśnienie oceny",
    "correct_answer": "poprawna odpowiedź lub pełne wyjaśnienie",
    "learning_tip": "edukacyjna wskazówka dla ucznia"
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/ai-quiz-master",
            "X-Title": "AI Quiz Master"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Jesteś mentorem. Oceniasz odpowiedzi uczniów w formacie JSON. Bądź konstruktywny i edukacyjny."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if attempt == max_retries:
                    raise ValueError(f"Błąd API ({e.response.status_code}): {e.response.text}")
                continue
            except httpx.RequestError as e:
                if attempt == max_retries:
                    raise ValueError(f"Błąd połączenia z API: {e}")
                continue

            result = response.json()
            print(f"[DEBUG] Odpowiedź API (ocena), próba {attempt}:", result)
            try:
                content = result["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                content = None
            if content:
                try:
                    return self._parse_json_response(content, Evaluation)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    continue
            # Jeśli content jest None, spróbuj ponownie
        # Po wszystkich próbach
        raise ValueError("Model nie zwrócił odpowiedzi po 3 próbach. Spróbuj ponownie później lub sprawdź API.")


# Globalna instancja klienta
_client: Optional[OpenRouterClient] = None

def get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client

def generate_question(topic: str, difficulty: str) -> Question:
    """Wygeneruj pytanie quizowe"""
    client = get_client()
    return client.generate_question(topic, difficulty)

def evaluate_answer(question: str, user_answer: str) -> Evaluation:
    """Oceń odpowiedź użytkownika"""
    client = get_client()
    return client.evaluate_answer(question, user_answer)
