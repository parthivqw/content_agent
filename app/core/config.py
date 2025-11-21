from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings and secrets.
    Automatically reads from the .env file.
    """
    GROQ_API_KEY:str
    A4F_API_KEY: str
    model_config=SettingsConfigDict(env_file='.env',env_file_encoding='utf-8',extra='ignore')

#Create a single, reusable instance of the settings
settings=Settings()