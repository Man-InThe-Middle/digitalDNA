from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name:str='DigitalDNA'; app_env:str='development'; debug:bool=True; api_host:str='127.0.0.1'; api_port:int=8000; require_authorization:bool=True; public_sources_only:bool=True; max_upload_mb:int=10
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
