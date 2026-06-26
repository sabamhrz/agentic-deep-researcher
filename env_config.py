import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import RunConfig
from agents.models.multi_provider import MultiProvider

PROJECT_ROOT = Path(__file__).parent

DEFAULT_MODEL = "poolside/laguna-m.1:free"
FALLBACK_MODELS = (
    "poolside/laguna-m.1:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)
WRITE_MODEL_CANDIDATES = FALLBACK_MODELS
WRITE_MAX_TOKENS = 2500
WRITE_TIMEOUT_SECONDS = 90
EMAIL_TIMEOUT_SECONDS = 30


def _clean(value: str | None) -> str:
    return (value or "").strip()


def load_env() -> None:
    """Load .env and normalize keys for OpenRouter, Gmail, and OpenAI-compatible clients."""
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    for key in list(os.environ):
        os.environ[key] = _clean(os.environ[key])

    openrouter_key = _clean(os.getenv("OPENROUTER_API_KEY"))
    openai_key = _clean(os.getenv("OPENAI_API_KEY"))

    if not openai_key and openrouter_key:
        os.environ["OPENAI_API_KEY"] = openrouter_key

    if openrouter_key and not _clean(os.getenv("OPENAI_BASE_URL")):
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

    if using_openrouter():
        os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "true")

    for key in ("GMAIL_APP_PASSWORD", "EMAIL_PASSWORD"):
        password = _clean(os.getenv(key))
        if password:
            os.environ[key] = password.replace(" ", "")

    if not _clean(os.getenv("GMAIL_EMAIL")) and _clean(os.getenv("EMAIL_FROM")):
        os.environ["GMAIL_EMAIL"] = os.environ["EMAIL_FROM"]

    if not _clean(os.getenv("GMAIL_APP_PASSWORD")) and _clean(os.getenv("EMAIL_PASSWORD")):
        os.environ["GMAIL_APP_PASSWORD"] = os.environ["EMAIL_PASSWORD"]

    if not _clean(os.getenv("RECIPIENT_EMAIL")) and _clean(os.getenv("EMAIL_TO")):
        os.environ["RECIPIENT_EMAIL"] = os.environ["EMAIL_TO"]


def has_llm_api_key() -> bool:
    return bool(_clean(os.getenv("OPENAI_API_KEY")))


def using_openrouter() -> bool:
    return bool(_clean(os.getenv("OPENROUTER_API_KEY")))


def get_model_name() -> str:
    return _clean(os.getenv("RESEARCH_MODEL")) or DEFAULT_MODEL


def get_model_candidates() -> list[str]:
    configured = get_model_name()
    candidates = [configured]
    for model in FALLBACK_MODELS:
        if model not in candidates:
            candidates.append(model)
    return candidates


def get_write_model_candidates() -> list[str]:
    """Prefer faster models for long report generation to avoid OpenRouter 504 timeouts."""
    configured = get_model_name()
    candidates: list[str] = []
    for model in (configured, *WRITE_MODEL_CANDIDATES):
        if model not in candidates:
            candidates.append(model)
    return candidates


def get_run_config() -> RunConfig:
    """Build a RunConfig that routes model calls through OpenRouter when configured."""
    if using_openrouter():
        provider = MultiProvider(
            openai_client=AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                default_headers={
                    "HTTP-Referer": _clean(os.getenv("OPENROUTER_SITE_URL")) or "http://localhost:7860",
                    "X-Title": _clean(os.getenv("OPENROUTER_APP_NAME")) or "Deep Research Agent",
                },
            ),
            openai_use_responses=False,
            openai_prefix_mode="model_id",
            unknown_prefix_mode="model_id",
        )
    else:
        provider = MultiProvider(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
            openai_use_responses=False,
            openai_prefix_mode="model_id",
            unknown_prefix_mode="model_id",
        )

    return RunConfig(
        model_provider=provider,
        tracing_disabled=using_openrouter(),
    )


load_env()
