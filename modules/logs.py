
import logging
import threading
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d] [Thread:%(threadName)s]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)

logging.getLogger("pyrogram").setLevel(logging.WARNING)


logger = logging.getLogger()


def thread_function(name):
    logger.info(f"Thread {name} starting")
    try:
    
        logger.debug(f"Thread {name} is working")
    except Exception as e:
        logger.error(f"An error occurred in thread {name}: {str(e)}")
    logger.info(f"Thread {name} finished")


threads = []
for i in range(5):
    thread = threading.Thread(target=thread_function, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

logger.info("All threads have finished.")
