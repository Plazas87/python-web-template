from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    secret_key: str = "change-me"
    access_token_expires_minutes: int = 60
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/{{ package_name }}_dev"
    file_storage_dir: str = "var/files"
    sentry_dsn: str = ""
    otel_exporter_otlp_endpoint: str = ""


settings = Settings()
