import logging
import os
import sys
from .config import LOG_FILE_SERVER, LOG_FILE_WISHES  # Importiere Pfade aus config


def setup_logging(logger_name, log_file):
    """Konfiguriert einen Logger und gibt ihn zurück."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Verhindert doppelte Handler bei erneutem Aufruf
    if not logger.handlers:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Erstelle die globalen Logger-Instanzen, die Services nutzen können
server_log = setup_logging('server_logger', LOG_FILE_SERVER)
wishes_log = setup_logging('wishes_logger', LOG_FILE_WISHES)