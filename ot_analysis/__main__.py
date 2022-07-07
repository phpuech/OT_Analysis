#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
main module to launch the optical tweezers curve analysis and classification tool
"""
import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from .view.mainview import View
from .controller.controller import Controller
from art import tprint


TODAY = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
DATA_DIR = os.path.expanduser('~') + os.sep + "OTanalysis_result_" + TODAY

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
