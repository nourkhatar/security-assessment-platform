import os
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError

from backend.ai.security_summary import (
    AIAnalysis,
    AIInput,
    build_security_prompt,
)


def _get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    invalid_values = {
        "",
        "your_api_key_here",
        "paste_your_real_key_here",
        "replace_me",
        "changeme",
    }

    if api_key.lower() in invalid_values:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Live AI analysis is unavailable."
        )

    return api_key


def analyze_security(
    data: AIInput,
    max_attempts: int = 3,
) -> AIAnalysis:
    api_key = _get_api_key()

    client = genai.Client(api_key=api_key)
    prompt = build_security_prompt(data)

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIAnalysis,
                ),
            )

            if response.parsed is not None:
                return response.parsed

            return AIAnalysis.model_validate_json(response.text)

        except ServerError:
            if attempt == max_attempts:
                raise

            delay = 2 ** (attempt - 1)

            print(
                f"Gemini temporarily unavailable "
                f"(attempt {attempt}/{max_attempts}). "
                f"Retrying in {delay}s..."
            )

            time.sleep(delay)

    raise RuntimeError("Gemini analysis failed unexpectedly.")
