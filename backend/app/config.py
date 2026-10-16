from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://bugtrack:bugtrack@localhost:5432/bugtrack"


settings = Settings()
