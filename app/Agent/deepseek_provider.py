"""DeepSeek model factory."""

from langchain_deepseek import ChatDeepSeek

from app.config import Settings, load_settings


def create_deepseek_model(settings: Settings | None = None) -> ChatDeepSeek:
    settings = settings or load_settings()
    return ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        api_base=settings.deepseek_api_base,
        temperature=0,
        timeout=60,
        max_retries=2,
    )
