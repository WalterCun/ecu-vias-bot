""" main.py """
import logging
from src.bot import start_bot

# Enable logging
logging.basicConfig(
    format="<%(lineno)d> [%(asctime)s] - [%(filename)s / %(funcName)s] - [%(levelname)s] -> %(message)s",
    level=logging.INFO
)

# set a higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    start_bot()

