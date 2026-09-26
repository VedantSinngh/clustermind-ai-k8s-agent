import logging
import sys

def setup_logging():
    try:
        from pythonjsonlogger import jsonlogger
        log_handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s'
        )
        log_handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.handlers = [log_handler]
        root_logger.setLevel(logging.INFO)
    except Exception:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
