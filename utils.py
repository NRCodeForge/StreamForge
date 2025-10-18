# StreamForge/utils.py

import logging
import os
import sys
from config import LOG_FILE_SERVER, LOG_FILE_WISHES



def setup_logging(logger_name, log_file):
    """Konfiguriert einen Logger und gibt ihn zurück, inklusive ConsoleHandler für Fehler."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if not logger.handlers:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # File Handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler NUR für Fehler (hilfreich für Debugging)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger




# Erstelle die globalen Logger-Instanzen, die Services nutzen können
server_log = setup_logging('server_logger', LOG_FILE_SERVER)
wishes_log = setup_logging('wishes_logger', LOG_FILE_WISHES)