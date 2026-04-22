from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings, loaded from .env file or environment variables."""
    
    # Binance API Settings
    binance_testnet_api_key: str = Field(default="", env="BINANCE_TESTNET_API_KEY")
    binance_testnet_api_secret: str = Field(default="", env="BINANCE_TESTNET_API_SECRET")
    binance_base_url: str = Field(default="https://testnet.binancefuture.com")
    binance_ws_url: str = Field(default="wss://stream.binancefuture.com/ws")
    
    # Execution & Risk Settings
    max_position_size: float = Field(default=1.0)
    max_leverage: int = Field(default=5)
    max_daily_loss_usdt: float = Field(default=100.0)
    
    # System Settings
    log_level: str = Field(default="INFO")
    db_path: str = Field(default="trading_bot.sqlite")
    
    # FastAPI Server
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global settings instance
settings = Settings()
