import httpx
from django.conf import settings


class AIServiceError(Exception):
    """Raised whenever the AI service can't be reached or returns an error."""
    pass


def _base_url() -> str:
    return getattr(settings, "AI_SERVICE_BASE_URL", "http://127.0.0.1:8001")


def _timeout() -> float:
    return getattr(settings, "AI_SERVICE_TIMEOUT_SECONDS", 8)


def ask_assistant(student_id: int, class_id: int, query_text: str, subject_id: int = None, interaction_mode: str = "chat") -> str:
    """
    Calls the FastAPI Student Assistant endpoint. Raises AIServiceError
    on any failure -- timeout, connection refused, or a non-2xx
    response -- so the calling Django view can catch ONE exception
    type and decide how to degrade gracefully, rather than needing to
    know about httpx's various exception classes directly.
    """
    payload = {
        "student_id": student_id, "class_id": class_id,
        "subject_id": subject_id, "query_text": query_text,
        "interaction_mode": interaction_mode,
    }
    try:
        response = httpx.post(
            f"{_base_url()}/api/ai/assistant/query",
            json=payload, timeout=_timeout(),
        )
        response.raise_for_status()
        return response.json()["response_text"]

    except httpx.TimeoutException:
        raise AIServiceError("AI Assistant timed out. Please try again.")
    except httpx.ConnectError:
        raise AIServiceError("AI service is currently unreachable.")
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"AI Assistant returned an error: {exc.response.text}")

def generate_question_paper(class_id: int, subject_id: int, topic: str, difficulty: str, question_count: int = 10) -> list[str]:
    payload = {
        "class_id": class_id, "subject_id": subject_id,
        "topic": topic, "difficulty": difficulty, "question_count": question_count,
    }
    try:
        response = httpx.post(
            f"{_base_url()}/api/ai/question-generator/generate",
            json=payload, timeout=_timeout(),
        )
        response.raise_for_status()
        return response.json()["questions"]
    except httpx.TimeoutException:
        raise AIServiceError("Question Paper Generator timed out. Please try again.")
    except httpx.ConnectError:
        raise AIServiceError("AI service is currently unreachable.")
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"Question Paper Generator returned an error: {exc.response.text}")


def ask_nl_to_sql(admin_id: int, query_text: str) -> dict:
    payload = {"admin_id": admin_id, "query_text": query_text}
    try:
        response = httpx.post(
            f"{_base_url()}/api/ai/query/ask",
            json=payload, timeout=_timeout(),
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        raise AIServiceError("NL-to-SQL Agent timed out. Please try again.")
    except httpx.ConnectError:
        raise AIServiceError("AI service is currently unreachable.")
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"NL-to-SQL Agent returned an error: {exc.response.text}")