import logging


def setup_logger(name, log_file, level=logging.INFO):
    """
    Set up a logger with the specified name, log file, and level.
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Example usage:
# logger = setup_logger('my_logger', 'my_log_file.log')
# logger.info('This is an info message')
