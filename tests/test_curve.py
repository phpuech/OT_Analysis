#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
Test Curve
"""
from os import sep
from ot_analysis.controller.controller import Controller


class TestCurve:
    """
    Class allowing to test the curve object
    """
    @classmethod
    def setup_class(cls):
        """
        This function is launched at each test to create the Controller object 
        and do the repetitive tasks before launching the test
        """
        print("setup")
        directory_test = 'tests' + sep + 'curves_test' + sep + 'verif'
        cls.controller = Controller(None, directory_test)
        cls.methods = {'threshold_align': 30, 'pulling_length': 50, 'model': 'linear',
                       'eta': 0.5, 'bead_radius': 1, 'factor_noise': 5, 'jump_force': 5,
                       'jump_point': 200, 'jump_distance': 200, 'drug': 'NaN', 'condition':
                       'NaN', 'optical': None, 'width_window_smooth': 151}
        cls.controller.create_dict_curves(cls.methods, cls.controller.files)
        cls.list_name_curve = list(cls.controller.dict_curve.keys())
        cls.curve = cls.controller.dict_curve[cls.list_name_curve[0]]

    def test_create_curve(self):
        """
        test the attributes of the curve object
        """
        assert self.curve.file == self.list_name_curve[0]
        assert len(self.curve.parameters_header) > 0
        assert len(self.curve.dict_segments) == 3
        assert len(self.curve.features) > 0

    def test_main_axis(self):
        """
        test the detection of the main axis
        """
        self.curve_main_axis = self.controller.dict_curve["b3c3-2021.06.07-12.07.20.873"]
        assert self.curve_main_axis.features["main_axis"]['axe'] == "x"
        assert self.curve_main_axis.features["main_axis"]['sign'] == "+"

    def test_correction_baseline(self):
        """
        test the detection of the baseline
        """
        assert 0.05 > float(
            self.curve.features['baseline_corrected_press (pN)']) > -0.05

    def test_corrected_std(self):
        """
        test the corrected standard deviation
        """
        assert 0.5 > float(
            self.curve.features['std_corrected_press (pN)']) > -0.5

    def test_ITU(self):
        """
        test if the curve is an infinite membrane tube
        """
        self.curve_itu = self.controller.dict_curve["b7c7-2019.05.07-18.29.57.187"]
        assert self.curve_itu.features['automatic_type'] == 'ITU'

    def test_FTU(self):
        """
        test if the curve is a finite membrane tube
        """
        self.curve_ftu = self.controller.dict_curve["b3c3-2021.06.07-12.07.20.873"]
        assert self.curve_ftu.features['automatic_type'] == 'FTU'

    def test_AD(self):
        """
        test if the curve is a adhesion
        """
        self.curve_ad = self.controller.dict_curve["b3c3-2021.06.07-14.58.15.777"]
        assert self.curve_ad.features['automatic_type'] == 'AD'

    def test_RE(self):
        """
        test if the curve is a rejected curve
        """
        self.curve_ad = self.controller.dict_curve["b4c4-2021.06.07-15.04.04.912"]
        assert self.curve_ad.features['automatic_type'] == 'RE'

    @classmethod
    def teardown_class(cls):
        """
        This function is run at the end of each test to destroy 
        all the elements created in the setup_class()
        """
        print("teardown")
        if cls.controller:
            del cls.controller
