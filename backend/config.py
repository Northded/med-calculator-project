import os
from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):

    DB_USER: str
    DB_NAME: str
    DB_PASS: str
    DB_PORT: int
    DB_HOST: str

    API_NINJAS_KEY: str
    API_NINJAS_ENABLED: bool 

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), "..", ".env"))


settings = Settings()
