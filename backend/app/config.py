import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Database ---
    # Works with either Postgres or MySQL. Example values:
    # Postgres: postgresql+psycopg2://user:password@localhost:5432/hcp_crm
    # MySQL:    mysql+pymysql://user:password@localhost:3306/hcp_crm
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/hcp_crm"
    )

    # --- Groq / LLM ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "gemma2-9b-it")
    GROQ_MODEL_LARGE: str = os.getenv("GROQ_MODEL_LARGE", "llama-3.3-70b-versatile")

    # --- App ---
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


settings = Settings()
