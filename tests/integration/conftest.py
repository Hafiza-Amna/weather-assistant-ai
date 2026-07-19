import pytest
import litellm
import os
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------

def _make_non_streaming_response(content: str = "Mocked Groq response!") -> litellm.ModelResponse:
    """Build a proper litellm ModelResponse for non-streaming calls."""
    return litellm.ModelResponse(
        id="mock-chatcmpl-001",
        model="groq/llama-3.3-70b-versatile",
        choices=[
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": None,
                },
            }
        ],
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    )


def _make_streaming_chunk(content: str = "Mocked Groq response!") -> litellm.ModelResponseStream:
    """Build a proper litellm ModelResponseStream chunk for streaming calls."""
    return litellm.ModelResponseStream(
        id="mock-chatcmpl-001",
        model="groq/llama-3.3-70b-versatile",
        choices=[
            {
                "index": 0,
                "finish_reason": "stop",
                "delta": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": None,
                },
            }
        ],
    )


@pytest.fixture(autouse=True)
def mock_litellm(monkeypatch):
    """Mock litellm.acompletion to return proper ModelResponse objects."""

    async def mock_acompletion(*args, **kwargs):
        if kwargs.get("stream", False):
            async def stream_generator():
                yield _make_streaming_chunk()
            return stream_generator()
        else:
            return _make_non_streaming_response()

    monkeypatch.setattr(litellm, "acompletion", mock_acompletion)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_dummy_key_for_tests")
    monkeypatch.setenv("LITELLM_DROP_PARAMS", "true")
