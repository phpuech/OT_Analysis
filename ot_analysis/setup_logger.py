from os import sep
import logging
from __init__ import DATA_DIR
from datetime import date, datetime
from pathlib import Path


def create_logger():
    """
    Creation of the log file with the desired configurations
    """
    today = str(date.today())
    time_today = str(datetime.now().time().replace(
        microsecond=0)).replace(':', '-')
    path_log = Path(DATA_DIR + sep + "Log")
    path_log.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.INFO,
                        filename=path_log.__str__() + sep + "otanalysis" + today +
                        '_' + time_today + ".log",
                        filemode="a",
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('logger_otanalysis')
