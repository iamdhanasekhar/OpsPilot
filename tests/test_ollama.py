
import asyncio

from app.services.ollama_service import OllamaService


async def main():
    ollama = OllamaService()

    result = await ollama.generate_json(
        system_prompt=(
            "You are a backend infrastructure expert. "
            "Return valid JSON only."
        ),
        user_prompt=(
            "Explain three common causes of HTTP 503 errors. "
            "Return JSON with a key called causes containing "
            "an array of three strings."
        ),
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
