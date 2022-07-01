#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
change a line in the misc.py file
from imp import reload by from importlib import reload

to eliminate this warning:
"DeprecationWarning: the imp module is deprecated in favour of importlib;"

file path:
~/anaconda3/lib/python3.9/site-packages/past/builtins/misc.py
"""


from os import sep
from ot_analysis.controller.controller import Controller


class TestController:
    """
    Test class of the controller for the application of processing of the optical tweezers curves
    """
    @classmethod
    def setup_class(cls):
        """
        This function is launched at each test to create the Controller object 
        and do the repetitive tasks before launching the test
        """
        print("setup")
        directory_test =  'tests' + sep + 'curves_test' + sep + 'verif'
        cls.controller = Controller(None, directory_test)
        methods = {'threshold_align': 30, 'pulling_length': 50, 'model': 'linear',
                   'eta': 0.5, 'bead_radius': 1, 'factor_noise': 5, 'jump_force': 5,
                   'jump_point': 200, 'jump_distance': 200, 'drug': 'NaN', 'condition':
                   'NaN', 'optical': None, 'width_window_smooth':151}
        cls.controller.create_dict_curves(methods)

    ######################################################################################

    def test_create_list_files(self):
        """
        Test that the create_list_files() function of the controller returns 
        a list of files to analyze
        """
        assert len(self.controller.files) > 0

    ######################################################################################

    def test_length_dict_curve(self):
        """
        Test that the length of the dictionary of curves of the controller after 
        analysis is not empty
        """
        assert len(self.controller.dict_curve) > 0

    ######################################################################################

    def test_incomplete_file(self):
        """
        Test the completeness of a curve file
        """
        file_incomplete = 'tests/curves_test/verif/b5c5-2021.06.07-15.10.03.254.jpk-nt-force'
        name_file = file_incomplete.split(sep)[-1]
        name_file = name_file.split('-')
        name_file = str(name_file[0][0:4]) + '-' + '-'.join(name_file[1:])
        new_curve, check_incomplete_file = Controller.create_object_curve(
            file_incomplete, name_file, 30, 50)
        assert new_curve == None and check_incomplete_file == True

    #########################################################################################

    def test_output(self, tmpdir):
        """
        Test the output of the output file temporarily

        :parameters:
            tmpdir: object
                allows you to create a temporary repository 
        """
        repository_output = tmpdir.mkdir('Result')
        name_file = self.controller.output_save(
            repository_output.__str__())
        print(name_file)
        with open(name_file, 'r') as file_test:
            assert file_test.readline()

    #########################################################################################

    @classmethod
    def teardown_class(cls):
        """
        This function is run at the end of each test to destroy 
        all the elements created in the setup_class()
        """
        print("teardown")
        if cls.controller:
            del cls.controller
