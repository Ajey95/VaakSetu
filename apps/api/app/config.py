from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMode(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


class ProviderReadiness(BaseModel):
    configured: bool
    blocking: bool
    mode: str
    missing: tuple[str, ...] = ()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_mode: AppMode = AppMode.SYNTHETIC
    public_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_api_key: str | None = None
    twilio_api_secret: str | None = None
    twilio_twiml_app_sid: str | None = None
    twilio_caller_id: str | None = None

    stt_provider: str = "deepgram"
    deepgram_api_key: str | None = None

    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    database_url: str | None = None
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None

    external_data_mode: str = "synthetic"
    general_search_api_key: str | None = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = False
    otel_exporter_otlp_endpoint: str | None = None

    def provider_readiness(self) -> dict[str, ProviderReadiness]:
        required: dict[str, tuple[str, ...]] = {
            "twilio": (
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_API_KEY",
                "TWILIO_API_SECRET",
                "TWILIO_TWIML_APP_SID",
                "TWILIO_CALLER_ID",
            ),
            "stt": ("DEEPGRAM_API_KEY",),
            "llm": ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL"),
            "database": ("DATABASE_URL",),
            "graph": ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"),
            "external_data": ("GENERAL_SEARCH_API_KEY",),
        }
        values = {
            "TWILIO_ACCOUNT_SID": self.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": self.twilio_auth_token,
            "TWILIO_API_KEY": self.twilio_api_key,
            "TWILIO_API_SECRET": self.twilio_api_secret,
            "TWILIO_TWIML_APP_SID": self.twilio_twiml_app_sid,
            "TWILIO_CALLER_ID": self.twilio_caller_id,
            "DEEPGRAM_API_KEY": self.deepgram_api_key,
            "LLM_PROVIDER": self.llm_provider,
            "LLM_API_KEY": self.llm_api_key,
            "LLM_MODEL": self.llm_model,
            "DATABASE_URL": self.database_url,
            "NEO4J_URI": self.neo4j_uri,
            "NEO4J_USERNAME": self.neo4j_username,
            "NEO4J_PASSWORD": self.neo4j_password,
            "GENERAL_SEARCH_API_KEY": self.general_search_api_key,
        }
        realtime = {"twilio", "stt", "llm"}
        report: dict[str, ProviderReadiness] = {}
        for provider, names in required.items():
            missing = tuple(name for name in names if not values[name])
            report[provider] = ProviderReadiness(
                configured=not missing,
                blocking=self.app_mode is AppMode.REAL and provider in realtime and bool(missing),
                mode=self.app_mode.value if missing else "real",
                missing=missing,
            )
        return report

