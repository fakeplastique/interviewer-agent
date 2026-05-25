from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "changeme-super-secret-key-32chars!!"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "AI Mock Interview"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_db"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_INTERVIEW_STARTED: str = "interview.started"
    KAFKA_TOPIC_ANSWER: str = "interview.answer"
    KAFKA_TOPIC_FEEDBACK: str = "interview.feedback"
    KAFKA_TOPIC_COMPLETED: str = "interview.completed"
    KAFKA_GROUP_ID: str = "interview-service"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"

    # ElevenLabs TTS
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"  # default: George

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Auth
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    @model_validator(mode="after")
    def _validate_production_secret_key(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == DEFAULT_SECRET_KEY:
                raise ValueError("SECRET_KEY must be overridden in production")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return self

    # Interview settings
    MAX_QUESTIONS_PER_INTERVIEW: int = 5


settings = Settings()
