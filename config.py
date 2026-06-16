from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str
    MAX_BOT_TOKEN: str

    ECM_BASE_URL: str = "https://itmoscow.educom.ru"
    ECM_REALM: str = "ecos-app"
    ECM_CLIENT_ID: str
    ECM_CLIENT_SECRET: str

    @property
    def ecm_token_url(self):
        return f"{self.ECM_BASE_URL}/ecos-idp/auth/realms/{self.ECM_REALM}/protocol/openid-connect/token"
    
    @property
    def ecm_records_base(self):
        return f"{self.ECM_BASE_URL}/gateway/api/records"


settings = Settings()