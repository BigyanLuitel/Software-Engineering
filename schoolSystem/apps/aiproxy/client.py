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