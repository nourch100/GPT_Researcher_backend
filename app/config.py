from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./research.db"
    OPENAI_API_KEY: str =""
    MISTRAL_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
  
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
