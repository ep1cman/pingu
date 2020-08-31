import logging
from pingu.plugin import Logger

logger = logging.getLogger("Log")

class Console(Logger):
    async def log(self, result):
        logger.info(result)  
