#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
File describing the instance class of the segment objects
"""
import pandas as pd


class Segment:
    """
    Class instantiating curve segment objects
    """

    def __init__(self, header_segment, data, name):
        """
        Initialization parameters of segment
        """
        self.name = name
        self.header_segment = header_segment
        self.data = data
        self.delta_time = 0
        self.corrected_data = pd.DataFrame()
        self.statistic_data = pd.DataFrame()
        self.features = {}
        # print(self.data['distance']*1e9)

    #########################################################################################

    def __str__(self):
        """
        Return function for a print of the object
        """
        return self.header_segment['segment-settings.duration']

    #########################################################################################

    def real_time(self):
        """
        Calculation of the time for a segment of the curve
        """
        print("real_time")
        # last_value = float(self.data['seriesTime'][len(self.data['seriesTime'])-1])
        # first_value = float(self.data['seriesTime'][0])
        last_value = float(self.data['time'][len(self.data['time'])-1])
        first_value = float(self.data['time'][0])
        self.delta_time = last_value - first_value
        # print(self.header_segment['segment-settings.duration'])
        # print(self.delta_time)
        return self.delta_time

    #########################################################################################

    def set_name(self, name):
        """
        Setter of the segment name

        :parameters:
            name: str
                name segment to be given
        """
        self.name = name

    #########################################################################################

    def check_alignment(self, main_axis, force_threshold):
        """
        Checking the alignment of the curve segment on the main axis

        :parameters:
            main_axis: str
                main axis of the manipulation
            seuil: float
                applied force defined at the beginning of the manipulation

        :return:
            check_align: bool
                True if misaligned on a secondary axis
        """
        # print("check_alignment")
        dict_align = {'AL': 'Yes', 'axe': []}
        axe = ''
        force_threshold = force_threshold
        baseline_no_main_axis = 0
        baseline_z = 0
        no_main_axis = ""
        if main_axis == 'x':
            no_main_axis = 'y'
        elif main_axis == 'y':
            no_main_axis = 'x'
        if self.name == 'Press':
            baseline_no_main_axis = abs(
                self.corrected_data[no_main_axis + 'Signal1'][0:1000].mean())
            baseline_z = abs(self.corrected_data['zSignal1'][0:1000].mean())
        elif self.name == 'Pull':
            baseline_no_main_axis = abs(
                self.corrected_data[no_main_axis + 'Signal1'][-1000:].mean())
            baseline_z = abs(self.corrected_data['zSignal1'][-1000:].mean())
        else:
            baseline_no_main_axis = 0
            baseline_z = 0

        if main_axis == 'x':
            min_value_no_main_axis = self.corrected_data['ySignal1'].min()
            max_value_no_main_axis = self.corrected_data['ySignal1'].max()
            delta_min_value_no_main_axis = min_value_no_main_axis - baseline_no_main_axis
            delta_max_value_no_main_axis = max_value_no_main_axis - baseline_no_main_axis
        elif main_axis == 'y':
            min_value_no_main_axis = self.corrected_data['xSignal1'].min()
            max_value_no_main_axis = self.corrected_data['xSignal1'].max()
            delta_min_value_no_main_axis = min_value_no_main_axis - baseline_no_main_axis
            delta_max_value_no_main_axis = max_value_no_main_axis - baseline_no_main_axis
        min_value_z = self.corrected_data['zSignal1'].min()
        max_value_z = self.corrected_data['zSignal1'].max()
        delta_min_value_z = min_value_z - baseline_z
        delta_max_value_z = max_value_z - baseline_z
        if delta_min_value_no_main_axis < -force_threshold:
            dict_align['axe'].append('-' + no_main_axis)
            dict_align['AL'] = 'No'
        # elif delta_value_no_main_axis > force_threshold:
        if delta_max_value_no_main_axis > force_threshold:
            dict_align['axe'].append('+' + no_main_axis)
            dict_align['AL'] = 'No'
        if delta_min_value_z < -force_threshold:
            dict_align['axe'].append('-z')
            dict_align['AL'] = 'No'
        if delta_max_value_z > force_threshold:
            dict_align['axe'].append('+z')
            dict_align['AL'] = 'No'
        if len(dict_align['axe']) == 0:
            dict_align['axe'] = 'NaN'
        return dict_align

    #########################################################################################

    def calcul_statistic(self, axe):
        """
        Retrieves all the statistical data for a given axis

        :parameters:
            axe: str
               the Axis whose statistical parameters are desired

        :return:
            self.statistic_data: Dataframe
                basic statistical parameters
        """
        statistic_data = self.data[axe.lower() + 'Signal1'].describe()
        self.statistic_data = statistic_data

    #########################################################################################
