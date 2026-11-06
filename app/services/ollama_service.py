
import json

import httpx

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class OllamaService:

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_predict": 1500,
            },
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                response.raise_for_status()

            response_data = response.json()

            content = response_data["message"]["content"]

            result = json.loads(content)

            if not isinstance(result, dict):
                raise ValueError(
                    "Ollama returned JSON, but the response is not an object"
                )

            return result

        except httpx.TimeoutException as exc:
            logger.error("Ollama request timed out")
            raise RuntimeError("Ollama request timed out") from exc

        except httpx.ConnectError as exc:
            logger.error("Unable to connect to Ollama")
            raise RuntimeError(
                "Unable to connect to Ollama. Check whether Ollama is running."
            ) from exc

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ollama returned HTTP error: %s",
                exc.response.status_code,
            )
            raise RuntimeError(
                f"Ollama returned HTTP {exc.response.status_code}"
            ) from exc

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.exception("Invalid response received from Ollama")
            raise RuntimeError(
                "Ollama returned an invalid JSON response"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception("Ollama communication failed")
            raise RuntimeError(
                "Ollama communication failed"
            ) from exc
