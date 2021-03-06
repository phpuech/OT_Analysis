#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
main module to launch the optical tweezers curve analysis and classification tool
"""
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from ot_analysis.view.mainview import View
from ot_analysis.controller.controller import Controller
from art import tprint

def main():
    """
    Launch application for curve analyis
    """
    # my_os = sys.platform
    tprint("OT_Analysis")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    view = View()
    controller = Controller(view)
    view.set_controller(controller)
    view.show()
    app.exec()

PATH_FILE = Path('data_test' + os.sep + 'txt' + os.sep)
PATH_FILE_JPK = Path("data_test" + os.sep + 'jpk_nt_force' + os.sep)
main()
