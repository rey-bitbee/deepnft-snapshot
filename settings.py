from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dingding_access_token: str
    dingding_secret: str
