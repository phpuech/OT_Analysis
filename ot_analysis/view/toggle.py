#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
Plan to build a custom Toggle button
"""

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import Qt, QRect, QPoint, QEasingCurve, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QFont


class QtToggle(QCheckBox):
    """
    Toggle Button instantiation class in the Qt interface

    :parameters:
        QCheckBox: heritage
            inheritance of the checkBox widget class
    """

    def __init__(self, width, height, bg_color, circle_color,
                 active_color, text, active_text, animation_curve=QEasingCurve.OutQuint):
        """
        Initialization of the Toggle object

        :parameters:
            width: int
                horizontal size of the button
            height: int
                height of the button
            bg_color: str
                background color when the button is in the OFF position
            circle_color: str
                color of the animation circle for the toggle state change
            active_color: str
                color when the button is in the ON position
            text: str
                text when the button is OFF
            active_text: str
                text when the button is ON
            animation_curve: object
                QEasingCurve.OutQuint by default
                animation during the transition of the button between two states
        """
        QCheckBox.__init__(self)
        # SET DEFAUT PARAMETERS
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        # Colors
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color
        self.inactive_text = text
        self.active_text = active_text

        # CREATE ANIMATION
        self._circle_position = 5
        self.animation = QPropertyAnimation(self, b'circle_position')
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(200)  # Time in millisecondes

        # Connect state changed
        self.stateChanged.connect(self.start_transition)

    # CREATE NEW SET AND GET PROPERTIE
    @pyqtProperty(int)  # GET
    def circle_position(self):
        """
        getter of the button position
        """
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        """
        setter of the button position
        """
        self._circle_position = pos
        self.update()

    def start_transition(self, value):
        """
        movement of the button according to the change of state

        :parameters:
            value: bool
                Button status
        """
        self.animation.setStartValue(self.circle_position)
        # self.animation.stop() # Stop animation if running
        if value:
            self.animation.setEndValue(self.width() - 27)
        else:
            self.animation.setEndValue(5)

        # START ANIMATION
        self.animation.start()

    def hitButton(self, pos: QPoint):
        """
        Position of the circle in the rectangle forming the toggle button

        :parameters:
            pos: object
                object representing a point in the plane
        """
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        """
        Drawing of the button including a rectangle with a point moving inside 
        according to a particular transition (left end to right end). 
        It also has a word centered on the opposite side of the point representing 
        the action to be performed  
        """
        # SET PAINTER
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # SET AS NO PEN
        painter.setPen(Qt.NoPen)

        # DRAW RECTANGLE
        rect = QRect(0, 0, self.width(), self.height())

        # CHECK IF IS CHECKED
        if not self.isChecked():
            # DRAW BG
            painter.setBrush(QColor(self._bg_color))
            painter.drawRoundedRect(
                0, 0, rect.width(), self.height(), self.height()//2, self.height()//2)

            # DRAW CIRCLE
            painter.setBrush(QColor(self._circle_color))
            painter.drawEllipse(self._circle_position, 3, 22, 22)

            # Write Text
            painter.setPen(QColor(self._active_color))
            painter.setFont(QFont('Arial Black', 11, QFont.Bold))

            taille_cadre = self.width()
            length_word = len(self.inactive_text)*10
            marge = -3
            if taille_cadre < 110:
                pos_x = taille_cadre - length_word + ((taille_cadre-110)//2)
            else:
                pos_x = taille_cadre - length_word - ((taille_cadre-110)//2)
            painter.drawText(int(pos_x), int(rect.height()//1.5), self.inactive_text)

        else:
            # DRAW BG
            painter.setBrush(QColor(self._active_color))
            painter.drawRoundedRect(
                0, 0, rect.width(), self.height(), self.height()/2, self.height()/2)

            # DRAW CIRCLE
            painter.setBrush(QColor(self._circle_color))
            painter.drawEllipse(self._circle_position, 3, 22, 22)

            # Write Text
            painter.setPen(QColor(self._bg_color))
            painter.setFont(QFont('Arial Black', 12, QFont.Bold))
            painter.drawText(5, int(rect.height()//1.5), self.active_text)

        # END DRAW
        painter.end()
