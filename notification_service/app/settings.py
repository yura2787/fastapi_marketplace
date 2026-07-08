from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    RMQ_HOST: str
    RMQ_PORT: int
    RMQ_VIRTUAL_HOST: str
    RMQ_USER: str
    RMQ_PASSWORD: str

    SMTP_SERVER: str
    USER: str
    TOKEN_UKR_NET: str

    class Config:
        env_file = ".env"


settings = Settings()
