#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
Classes of intanciation of the secondary window for the display of the automatic classification
"""

from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout


class Infowindow(QWidget):
    """
    Instantiation of info window
    """
    def __init__(self, parent=None):
        """
        Secondary window constructor
        """
        super(Infowindow, self).__init__(parent)
        self.title = QLabel(" Loading Data...")
        self.nb_curve = QLabel("0/6")
        self.info_curve = QLabel("")
        self.setWindowTitle(u'Processing data')
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.title)
        self.setLayout(self.main_layout)

    #################################################################

    def set_nb_curve(self, nb):
        """
        setter of the 'nb_curve' widget text
        """
        self.nb_curve.setText(nb)
        self.main_layout.addWidget(self.nb_curve)
        self.show()

    ##################################################################

    def set_info_curve(self, text):
        """
        setter of the 'info_curve' widget text
        """
        self.info_curve.setText(text)
        self.main_layout.addWidget(self.info_curve)
        self.show()
    
    ###################################################################
    
    def set_title(self, text='Loading is done'):
        """
        setter of the 'title' widget text
        """
        self.title.setText(text)
