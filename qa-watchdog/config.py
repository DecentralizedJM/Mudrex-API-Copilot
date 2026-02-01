"""
QA Watchdog Bot Configuration

Environment variables for the QA service.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for QA Watchdog Bot"""
    
    # Telegram
    QA_TELEGRAM_BOT_TOKEN: str
    QA_TEST_GROUP_ID: int
    COPILOT_BOT_USERNAME: str
    ADMIN_USERNAME: str
    
    # Gemini
    QA_GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Redis (optional, for history tracking)
    REDIS_URL: Optional[str] = None
    
    # Timing
    RESPONSE_TIMEOUT: int = 60  # seconds to wait for copilot response
    TEST_INTERVAL: int = 30  # seconds between tests
    
    # Scheduler
    DAILY_QA_HOUR: int = 3  # UTC hour for full daily QA suite
    DAILY_QA_MINUTE: int = 0
    CRITICAL_TEST_INTERVAL_HOURS: int = 6
    SPOT_CHECK_INTERVAL_HOURS: int = 2
    
    # Test counts
    DAILY_TEST_COUNT: int = 20
    CRITICAL_TEST_COUNT: int = 5
    SPOT_CHECK_COUNT: int = 2
    
    # Reports
    REPORTS_DIR: str = "qa-watchdog/reports"
    DATA_DIR: str = "qa-watchdog/data"
    
    # Health check
    HEALTH_PORT: int = 8081
    
    # Bot startup - delay before polling to let old instance shut down (avoids Conflict)
    BOT_STARTUP_DELAY: int = 30
    
    # Run a spot check on startup to verify setup (set RUN_QA_ON_STARTUP=1)
    RUN_QA_ON_STARTUP: bool = False
    
    # Direct API - Telegram doesn't deliver bot-to-bot messages, so call Copilot HTTP API
    COPILOT_QA_URL: Optional[str] = None  # e.g. https://mudrex-api-copilot.up.railway.app
    QA_API_SECRET: Optional[str] = None  # Must match Copilot's QA_API_SECRET
    
    @classmethod
    def _get_env(cls, key: str, fallback_key: Optional[str] = None, fallback_keys: Optional[list[str]] = None, default: Optional[str] = None) -> str:
        """Get env var with optional fallbacks (Railway may use different names)."""
        val = os.environ.get(key)
        if val:
            return val
        for fk in [fallback_key] if fallback_key else []:
            val = os.environ.get(fk)
            if val:
                return val
        for fk in fallback_keys or []:
            val = os.environ.get(fk)
            if val:
                return val
        if default is not None:
            return default
        raise KeyError(key)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            QA_TELEGRAM_BOT_TOKEN=cls._get_env("QA_TELEGRAM_BOT_TOKEN"),  # Must be QA bot's own token
            QA_TEST_GROUP_ID=int(cls._get_env("QA_TEST_GROUP_ID", fallback_key="TEST_GROUP_ID", default="-1003269114897")),
            COPILOT_BOT_USERNAME=os.environ.get("COPILOT_BOT_USERNAME", "API_Assistant_V2_bot"),
            ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "DecentralizedJM"),
            QA_GEMINI_API_KEY=cls._get_env("QA_GEMINI_API_KEY", fallback_keys=["GEMINI_API_KEY", "QA_GEMINI_KEY"]),
            GEMINI_MODEL=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            REDIS_URL=os.environ.get("REDIS_URL"),
            RESPONSE_TIMEOUT=int(os.environ.get("RESPONSE_TIMEOUT", "60")),
            TEST_INTERVAL=int(os.environ.get("TEST_INTERVAL", "30")),
            DAILY_QA_HOUR=int(os.environ.get("DAILY_QA_HOUR", "3")),
            DAILY_QA_MINUTE=int(os.environ.get("DAILY_QA_MINUTE", "0")),
            CRITICAL_TEST_INTERVAL_HOURS=int(os.environ.get("CRITICAL_TEST_INTERVAL_HOURS", "6")),
            SPOT_CHECK_INTERVAL_HOURS=int(os.environ.get("SPOT_CHECK_INTERVAL_HOURS", "2")),
            DAILY_TEST_COUNT=int(os.environ.get("DAILY_TEST_COUNT", "20")),
            CRITICAL_TEST_COUNT=int(os.environ.get("CRITICAL_TEST_COUNT", "5")),
            SPOT_CHECK_COUNT=int(os.environ.get("SPOT_CHECK_COUNT", "2")),
            REPORTS_DIR=os.environ.get("REPORTS_DIR", "qa-watchdog/reports"),
            DATA_DIR=os.environ.get("DATA_DIR", "qa-watchdog/data"),
            # Railway injects PORT; use it so healthcheck works
            HEALTH_PORT=int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8081"))),
            BOT_STARTUP_DELAY=int(os.environ.get("BOT_STARTUP_DELAY", "30")),
            RUN_QA_ON_STARTUP=os.environ.get("RUN_QA_ON_STARTUP", "").lower() in ("1", "true", "yes"),
            COPILOT_QA_URL=os.environ.get("COPILOT_QA_URL") or os.environ.get("COPILOT_URL") or None,
            QA_API_SECRET=os.environ.get("QA_API_SECRET") or None,
        )
    
    def validate(self) -> None:
        """Validate required configuration"""
        if not self.QA_TELEGRAM_BOT_TOKEN:
            raise ValueError("QA_TELEGRAM_BOT_TOKEN is required")
        if not self.QA_GEMINI_API_KEY:
            raise ValueError("QA_GEMINI_API_KEY is required")
        if not self.QA_TEST_GROUP_ID:
            raise ValueError("QA_TEST_GROUP_ID is required")


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get or create config instance"""
    global config
    if config is None:
        config = Config.from_env()
        config.validate()
    return config
