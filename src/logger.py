import logging
from config import LOG_LEVEL

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)
