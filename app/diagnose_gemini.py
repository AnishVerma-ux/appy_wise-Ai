from google import genai

from app.core.config import settings


def main() -> None:
    print(
        "API key loaded:",
        bool(settings.gemini_api_key),
    )
    print("Configured model:", settings.gemini_model)

    if settings.gemini_api_key is None:
        print("ERROR: GEMINI_API_KEY is missing")
        return

    try:
        client = genai.Client(
            api_key=(
                settings.gemini_api_key.get_secret_value()
            )
        )

        response = client.interactions.create(
            model=settings.gemini_model,
            input="Reply with only the word OK.",
            store=False,
        )

        print("SUCCESS:", response.output_text)

    except Exception as exc:
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR MESSAGE:", str(exc))


if __name__ == "__main__":
    main()