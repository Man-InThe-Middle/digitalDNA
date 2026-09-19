from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DigitalDNA"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "sqlite:///./digitaldna.db"
    llm_provider: str = "local"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:8b"
    require_authorization: bool = True
    public_sources_only: bool = True
    allow_private_access: bool = False
    allow_credential_collection: bool = False
    allow_access_control_bypass: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
