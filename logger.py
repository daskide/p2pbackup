import logging


def prepare_logger(source):
    logging.basicConfig(format=f'{source}:%(levelname)s: %(message)s', level=logging.INFO)
    logging.info("Started")