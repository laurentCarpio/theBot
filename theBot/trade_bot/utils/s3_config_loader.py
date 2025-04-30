import boto3
import json
import threading
from typing import Any, Callable
from datetime import datetime, timedelta
from trade_bot.utils.trade_logger import logger


class S3ConfigLoader:
    def __init__(self, bucket: str, key: str, auto_load: bool = True):
        self.bucket = bucket
        self.key = key
        self.s3 = boto3.client("s3")
        self._config = {}
        self._refresh_timer = None
        self._refresh_callback: Callable[[], None] = None

        if auto_load:
            self.load_config()  # Load config immediately
            self._schedule_refresh()  # Schedule based on loaded values

    def load_config(self) -> None:
        """Fetch and load the JSON config from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
            content = response["Body"].read().decode("utf-8")
            self._config = json.loads(content)
            logger.info(f"✅ Config loaded from S3 at {datetime.now()}")
            logger.debug(f"🔍 Config contents: {self._config}")  # ✅ Optional debug log

            if self._refresh_callback:  # Trigger dynamic updates (e.g. log level)
                self._refresh_callback()

        except Exception as e:
            logger.error(f"❌ Failed to load config from S3: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Access a config value by key."""
        return self._config.get(key, default)

    def reload(self) -> None:
        """Force reloading config from S3 and reschedule refresh."""
        self.load_config()
        self._schedule_refresh()

    def as_dict(self) -> dict:
        """Get the whole config as a dictionary."""
        return self._config

    def set_refresh_callback(self, callback: Callable[[], None]) -> None:
        """Set a function to call after config is refreshed."""
        self._refresh_callback = callback

    def _schedule_refresh(self):
        """Schedule the next refresh based on delay (Xh Ym Zs) from now."""
        refresh_hours = int(self.get("CONFIG_REFRESH_HOUR", 1))
        refresh_minutes = int(self.get("CONFIG_REFRESH_MINUTE", 0))
        refresh_seconds = int(self.get("CONFIG_REFRESH_SECOND", 0))

        delay = timedelta(
            hours=refresh_hours,
            minutes=refresh_minutes,
            seconds=refresh_seconds
        )

        next_refresh = datetime.now() + delay
        seconds_until_refresh = delay.total_seconds()

        logger.debug(f"🛠 Using refresh delay from config: {delay}")
        logger.info(f"⏰ Next config refresh scheduled for {next_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

        self._refresh_timer = threading.Timer(seconds_until_refresh, self.reload)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()