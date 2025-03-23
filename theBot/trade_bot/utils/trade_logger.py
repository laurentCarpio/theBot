import logging.config
from trade_bot.utils.enums import CONFIG_LOG_FILE

logging.config.fileConfig(CONFIG_LOG_FILE)
logger = logging.getLogger()
logger.info("Logging is configured!")
