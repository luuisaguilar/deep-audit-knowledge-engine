import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Sets up structured-ish console logging for DocGrab.
    """
    logger = logging.getLogger("docgrab")
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return
        
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
