from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://filmdb:filmdb@localhost:5432/filmdb"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"


settings = Settings()
