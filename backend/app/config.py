from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Workforce Management System API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # These must come from the .env file (or Vercel environment variables)
    MONGODB_URL: str = ""
    DATABASE_NAME: str = "enterprise_workforce_db"

    # Browser-facing CORS allowlist for the trusted local development frontend origins used by this project.
    CORS_ALLOWED_ORIGINS: str = (
        "http://127.0.0.1:4173,http://localhost:4173,"
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:5174,http://localhost:5174,"
        "http://127.0.0.1:5175,http://localhost:5175,"
        "http://127.0.0.1:3000,http://localhost:3000"
    )

    # IMPORTANT: Provide a strong secret via environment (do NOT commit to source).
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_BOOTSTRAP_PASSWORD: str = ""

    # Gemini API key comes from .env
    GEMINI_API_KEY: str = ""

    # Timezone convention used for attendance, leaves, shifts, and automation comparisons.
    # The project uses UTC consistently for scheduler and business-time comparisons.
    APP_TIMEZONE: str = "UTC"

    # Automation engine configuration
    # Disable automation scheduler by default in serverless environments (Vercel)
    AUTOMATION_ENABLED: bool = False
    # Attendance reconciliation: run every N minutes when enabled
    ATTENDANCE_RECONCILIATION_INTERVAL_MINUTES: int = 15

    # GPS attendance geofence configuration
    OFFICE_LATITUDE: float = 0.0
    OFFICE_LONGITUDE: float = 0.0
    OFFICE_GEOFENCE_RADIUS_METERS: float = 200.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()