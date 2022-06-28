import sys
import os
from datetime import datetime

TODAY = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
DATA_DIR = os.path.expanduser('~') + os.sep + "OTanalysis_result_" + TODAY
