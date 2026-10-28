from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_base_url: str = "http://localhost:8000"
    btc_address: str = "bc1qj0s0ghvzjqtcfcgcp5ayqc3taydyksu64c6gaq"
    btc_price_usd: float = 9.00
    btc_confirmations: int = 1
    btc_api: str = "https://mempool.space/api"

    storage: str = "local"
    local_storage_dir: str = "./storage"
    s3_bucket: str = ""
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_public_base: str = ""

    db_path: str = "./camhighlevel.db"
    admin_token: str = "change-moi-svp"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    class Config:
        env_file = ".env"

settings = Settings()