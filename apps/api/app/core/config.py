from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TuTu Apply API"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    openai_api_key: str | None = None
    temporal_host: str = "localhost:7233"
    temporal_task_queue: str = "tutu-phase1"


settings = Settings()
