#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
File describing the instance class of the optical effect objects
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


class OpticalEffect:
    """
    Construction plan of an optical effect correction on a curved object
    """

    def __init__(self, curve):
        self.curve = curve
        self.segment_press = self.curve.dict_segments['Press']
        self.segment_pull = self.curve.dict_segments['Pull']
        self.initialization_data()

    def initialization_data(self):
        """
        Recovery of all segment data for optical corrections
        """
        self.force_data_press = self.segment_press.corrected_data[
            self.curve.features['main_axis']['axe'] + 'Signal1']
        self.force_data_press_copy = self.force_data_press.copy()
        self.force_data_pull = self.segment_pull.corrected_data[
            self.curve.features['main_axis']['axe'] + 'Signal1']
        self.force_data_pull_copy = self.force_data_pull.copy()
        self.time_data_press = self.segment_press.corrected_data['seriesTime'].copy(
        )
        self.time_data_pull = self.segment_pull.corrected_data['seriesTime'].copy(
        )
        self.force_smooth_press = self.curve.smooth(
            self.force_data_press)
        self.force_smooth_press_copy = self.force_smooth_press.copy()

    def fitting_and_contact_theorical(self, segment, tolerance):
        """
        fitting piecewise curves to determine the theoretical contact point.

        :parameters:
            segment: str
                name of the segment to analyze
            tolerance: int
                number of times the tolerated standard deviation (threshold for determining the contact point)
        :return:
            coor_x_contact_point_extrapolated: float
                theoretical time value of the artificial contact point (not on the curve)
            coor_y_contact_point_extrapolated: float
                theoretical force value of the artificial contact point (not on the curve)
            baseline_force_data: list(array)
                artificial data vector representing the baseline
            fitted: list(array)
                artificial data vector representing the fitter force
            length_end: int
                length for fitter data (end for "Press" segment and start for "Pull" segment)
        """
        if segment == 'Press':
            force_data_start = self.force_data_press[0:3000].reset_index(
                drop=True)
            force_data_end = self.force_data_press[-600:].reset_index(
                drop=True)
            time_data_start = self.time_data_press[0:3000].reset_index(
                drop=True)
            time_data_end = self.time_data_press[-600:].reset_index(drop=True)
            index_contact = self.curve.retrieve_contact(
                self.force_data_press, segment, tolerance)
            length_end = len(self.force_data_press[index_contact[0]:])
            baseline = force_data_start.mean()
            baseline_force_data = np.full(len(self.force_data_press), baseline)
            f_param = curve_fit(self.curve.linear_fit,
                                time_data_end, force_data_end)
            fitted = self.curve.linear_fit(
                self.time_data_press[-length_end:], f_param[0][0], f_param[0][1])
            coor_x_contact_point_extrapolated = (
                f_param[0][1] - baseline)/(-f_param[0][0])
            coor_y_contact_point_extrapolated = f_param[0][0] * \
                coor_x_contact_point_extrapolated + f_param[0][1]
            value_contact_point_theorical = self.time_data_press[self.time_data_press >=
                                                                 coor_x_contact_point_extrapolated]
            if len(value_contact_point_theorical) > 0:
                list_index = value_contact_point_theorical.index
                index_contact_point_theorical = list_index[0]
            # value_contact_point_theorical = value_contact_point_theorical.reset_index(drop=True)
            # if len(value_contact_point_theorical) > 0:
            #     value_contact_point_theorical = value_contact_point_theorical[0]
            # index_contact_point_theorical = np.where(self.time_data_press == value_contact_point_theorical)[0][0]
            # print(index_contact_point_theorical)
                self.curve.graphics['contact_theorical_press'] = {
                    'index': index_contact_point_theorical, 'value': self.force_data_press[index_contact_point_theorical]}

        elif segment == 'Pull':
            start_point = 0
            if self.curve.features['force_min_curve']['value'] > self.curve.features['force_min_press']['value']:
                start_point = self.curve.features['force_min_curve']['index']
            length_end = len(
                self.force_data_pull[start_point:self.curve.features['force_max_curve']['index']])
            force_data_end = self.force_data_pull[-3000:].reset_index(
                drop=True)
            force_data_start = self.force_data_pull[start_point:500].reset_index(
                drop=True)
            time_data_end = self.time_data_pull[-3000:].reset_index(drop=True)
            time_data_start = self.time_data_pull[start_point:500].reset_index(
                drop=True)
            baseline = force_data_end.mean()
            baseline_force_data = np.full(len(self.force_data_pull), baseline)
            f_param = curve_fit(self.curve.linear_fit,
                                time_data_start, force_data_start)
            fitted = self.curve.linear_fit(
                self.time_data_pull[start_point:length_end], f_param[0][0], f_param[0][1])
            coor_x_contact_point_extrapolated = (
                f_param[0][1] - baseline)/(-f_param[0][0])
            coor_y_contact_point_extrapolated = f_param[0][0] * \
                coor_x_contact_point_extrapolated + f_param[0][1]
            value_contact_point_theorical = self.time_data_pull[self.time_data_pull <=
                                                                coor_x_contact_point_extrapolated].reset_index(drop=True)
            value_contact_point_theorical = value_contact_point_theorical[len(
                value_contact_point_theorical)-1]
            index_contact_point_theorical = np.where(
                self.time_data_pull == value_contact_point_theorical)[0][0]
            self.curve.graphics['contact_theorical_pull'] = {
                'index': index_contact_point_theorical, 'value': self.force_data_pull[index_contact_point_theorical]}
        return coor_x_contact_point_extrapolated, coor_y_contact_point_extrapolated, baseline_force_data, fitted, length_end

    def manual_correction(self, fig, tolerance):
        """
        creation of the figure to select the area for the optical correction

        :parameters:
            fig: object
                figure to which add the visualization axes
            tolerance: int
                number of times the tolerated standard deviation (threshold for determining the contact point)

        :return:
            fig: object
                the figure with the two axes of uncorrected data
        """
        print('manual_correction')
        force_data_press_copy = self.force_data_press_copy.copy()
        force_data_pull_copy = self.force_data_pull_copy.copy()
        std = float(self.curve.features['std_corrected_press (pN)'])
        # if len(self.curve.dict_segments) == 2:
        coor_x_contact_point_extrapolated_press, coor_y_contact_point_extrapolated_press, baseline_force_data_press,\
            fitted_press, length_stop_press = self.fitting_and_contact_theorical(
                'Press', tolerance)

        coor_x_contact_point_extrapolated_pull, coor_y_contact_point_extrapolated_pull, baseline_force_data_pull,\
            fitted_pull, length_stop_pull = self.fitting_and_contact_theorical(
                'Pull', tolerance)

        ax1 = fig.add_subplot(221)
        ax1.plot(self.time_data_press, force_data_press_copy,
                 picker=True, pickradius=1)
        ax1.plot(self.time_data_press, baseline_force_data_press)
        ax1.plot(self.time_data_press[-length_stop_press:], fitted_press)
        ax1.plot(coor_x_contact_point_extrapolated_press, coor_y_contact_point_extrapolated_press,
                 marker='D', color='yellow', label='contact point extrapolated')
        if 'contact_theorical_press' in self.curve.graphics:
            ax1.plot(self.time_data_press[self.curve.graphics['contact_theorical_press']['index']], force_data_press_copy[
                self.curve.graphics['contact_theorical_press']['index']], marker='o', color='brown', label='contact_theorical')
        else:
            ax1.plot(self.time_data_press[self.curve.features['contact_point']['index']], force_data_press_copy[
                self.curve.features['contact_point']['index']], marker='o', color='brown', label='contact_theorical')
        ax1.set_ylabel('force (pN')
        ax1.set_xlabel('time (s)')

        ax2 = fig.add_subplot(222)
        ax2.plot(self.time_data_pull, force_data_pull_copy)
        ax2.plot(self.time_data_pull, baseline_force_data_pull)
        ax2.plot(self.time_data_pull[:length_stop_pull], fitted_pull)
        ax2.plot(coor_x_contact_point_extrapolated_pull, coor_y_contact_point_extrapolated_pull,
                 marker='D', color='yellow', label='contact point extrapolated')
        ax2.plot(self.time_data_pull[self.curve.graphics['contact_theorical_pull']['index']],
                 force_data_pull_copy[self.curve.graphics['contact_theorical_pull']['index']], marker='o', color='brown', label='contact_theorical')
        ax2.set_ylabel('force (pN)')
        ax2.set_xlabel('time (s)')

        return fig

    def automatic_correction(self, tolerance):
        """
        Management of the automatic correction of the optical effect on the "Press" segment 
        on the data between the beginning and the contact point

        :parameters:
            tolerance: int
                number of times the tolerated standard deviation (threshold for determining the contact point)
        """
        print('automatic correction')
        # if len(self.curve.dict_segments) == 2:
        coor_x_contact_point_extrapolated_press, coor_y_contact_point_extrapolated_press, baseline_force_data_press,\
            fitted_press, length_stop_press = self.fitting_and_contact_theorical(
                'Press', tolerance)
        coor_x_contact_point_extrapolated_pull, coor_y_contact_point_extrapolated_pull, baseline_force_data_pull,\
            fitted_pull, length_stop_pull = self.fitting_and_contact_theorical(
                'Pull', tolerance)
        index_contact_point__theo_press = self.curve.graphics['contact_theorical_press']['index']
        index_contact_point_theo_pull = self.curve.graphics['contact_theorical_pull']['index']

        force_data_press_part = self.force_data_press.loc[:index_contact_point__theo_press]
        time_data_press_part = self.time_data_press.loc[:index_contact_point__theo_press]
        force_smooth_press = pd.Series(self.force_smooth_press)
        force_smooth_part = force_smooth_press.loc[:index_contact_point__theo_press]

        force_data_pull_part = self.force_data_pull.loc[index_contact_point_theo_pull:]
        time_data_pull_part = self.time_data_pull.loc[index_contact_point_theo_pull:]

        self.force_data_press.update(
            self.force_data_press-force_smooth_part)
        list_index = list(force_data_pull_part.index)
        list_value = list(force_smooth_part)
        list_value = [num for num in reversed(list_value)]
        if len(list_value) < len(list_index):
            list_index = list_index[:len(list_value)]
        else:
            list_value = list_value[:len(list_index)]
        data_subtract = pd.DataFrame(list_value, index=list_index)
        self.force_data_pull.update(
            self.force_data_pull - data_subtract[0])

    def correction_optical_effect(self, list_ind_correction, fig):
        """
        Management of the manual correction of the optical effect on the segment "Press" on the data between the two points chosen by the user

        :parameters:
            list_ind_correction: list
                list of length 2 with the coordinates of the points chosen by the user (start point of the data range and end point)
            fig: object
                the figure to be modified for the visualization of the modification 
        """
        force_data_pull_copy = self.force_data_pull_copy.copy()
        if 'contact_theorical_press' in self.curve.graphics:
            index_contact_point_press = self.curve.graphics['contact_theorical_press']['index']
        else:
            index_contact_point_press = self.curve.features['contact_point']['index']
        index_contact_point_pull = self.curve.graphics['contact_theorical_pull']['index']
        force_smooth = pd.Series(self.force_smooth_press_copy)
        data_range_press = force_smooth.loc[list_ind_correction[0]:list_ind_correction[1]]
        delta_i2_press = 0
        delta_i2_pull = 0
        add_force_data_pull = 0
        delta_i1_press = index_contact_point_press - list_ind_correction[0]
        if index_contact_point_press > list_ind_correction[1]:
            delta_i2_press = index_contact_point_press - list_ind_correction[1]
            delta_i1_press = delta_i1_press - delta_i2_press*2
            delta_i1_pull = index_contact_point_pull + delta_i1_press
        else:
            delta_i2_press = list_ind_correction[1] - index_contact_point_press
            delta_i1_pull = index_contact_point_pull + delta_i1_press
        if delta_i1_pull > len(force_data_pull_copy):
            add_force_data_pull = delta_i1_pull - len(force_data_pull_copy)
        if delta_i2_press > index_contact_point_pull:
            delta_i2_pull = 0
            difference = delta_i2_press - index_contact_point_pull
            delta_i1_pull = delta_i1_pull + difference
        else:
            delta_i2_pull = index_contact_point_pull - delta_i2_press
        data_range_pull = force_data_pull_copy.loc[delta_i2_pull:delta_i1_pull]
        list_index = list(data_range_pull.index)
        list_value = []
        if add_force_data_pull != 0:
            list_value = list(data_range_press)
            # print(len(list_index))
            # print(len(list_value))
            list_value = list_value[:len(list_index)]
        else:
            list_value = list(data_range_press)
        list_value = [num for num in reversed(list_value)]
        data_subtract = pd.DataFrame(list_value, index=list_index)
        dict_param = {'list_ind_correction': list_ind_correction, 'index_contact_point_press': index_contact_point_press,
                      'index_contact_point_pull': index_contact_point_pull, 'list_index': list_index, 'data_range_press': data_range_press,
                      'data_subtract': data_subtract}

        self.plot_correction_manual(fig, dict_param)

    def plot_correction_manual(self, fig, dict_param):
        """
        creation of graphics allowing the visualization of the manual correction of the optical effect

        :parameters:
            fig: object
                the figure to be modified for the visualization of the modification
            dict_param: dict
                dictionary containing all the coordinates of the points either to be used for modification or to be displayed on the curves
        """
        force_data_press_copy = self.force_data_press_copy.copy()
        force_data_pull_copy = self.force_data_pull_copy.copy()
        index_contact_point__exp_press = self.curve.features['contact_point']['index']
        index_contact_point_exp_pull = self.curve.features['point_release']['index']
        force_smooth = pd.Series(self.force_smooth_press_copy)
        y_lim = (self.curve.features['force_min_curve']['value']-2,
                 self.curve.features['force_max_curve']['value'] + 2)
        ax1 = fig.axes[0]
        for element in ax1.lines:
            if element.get_marker() == 'D' and element.get_label() != 'contact point extrapolated':
                element.set_marker("")
        ax1.set_title('segment Press')
        ax1.set_ylim(y_lim)
        ax1.plot(self.time_data_press, force_smooth,
                 color="#80cdc1", label='smooth')
        #ax1.plot(self.time_data_press[index_contact_point__exp_press], self.force_data_press_copy[index_contact_point__exp_press], marker='D', color='cyan')
        ax1.plot(self.time_data_press[dict_param['index_contact_point_press']],
                 force_data_press_copy[dict_param['index_contact_point_press']], marker='D', color='brown', label='contact point')
        ax1.plot(self.time_data_press[dict_param['list_ind_correction'][0]],
                 force_data_press_copy[dict_param['list_ind_correction'][0]], marker='o', color='#08CC0A', label="first point intreval")
        ax1.plot(self.time_data_press[dict_param['list_ind_correction'][1]],
                 force_data_press_copy[dict_param['list_ind_correction'][1]], marker='o', color='red', label="last point intreval")
        ax1.legend(loc='lower left')

        ax2 = fig.axes[1]
        ax2.plot(self.time_data_pull[dict_param['index_contact_point_pull']],
                 force_data_pull_copy[dict_param['index_contact_point_pull']], marker='D', color='brown', label='contact point')
        #ax2.plot(self.time_data_pull[index_contact_point_exp_pull], self.force_data_pull_copy[index_contact_point_exp_pull], marker='D', color='cyan')
        ax2.plot(self.time_data_pull[dict_param['list_index'][0]], force_data_pull_copy[dict_param['list_index']
                 [0]], marker='o', color='red', label="first point intreval")
        ax2.plot(self.time_data_pull[dict_param['list_index'][-1]], force_data_pull_copy[dict_param['list_index']
                 [-1]], marker='o', color='#08CC0A', label='last point intreval')
        ax2.set_ylabel('force (pN)')
        ax2.set_xlabel('time (s)')
        ax2.set_ylim(y_lim)
        ax2.set_title('segment Pull')
        ax2.legend(loc='lower right')

        ax3 = fig.add_subplot(223)
        ax3.plot(self.time_data_press, force_data_press_copy)
        ax3.set_ylabel('force (pN)')
        ax3.set_xlabel('time (s)')
        ax3.set_ylim(y_lim)

        ax4 = fig.add_subplot(224)
        ax4.plot(self.time_data_pull, force_data_pull_copy)
        ax4.set_ylabel('force (pN)')
        ax4.set_xlabel('time (s)')
        ax4.set_ylim(y_lim)
        force_data_press_copy.update(
            force_data_press_copy - dict_param['data_range_press'])
        if self.curve.features['force_min_curve']['value'] < self.curve.features['force_min_press']['value'] and dict_param['data_subtract'][0].index[0] == 0:
            list_range = list(
                range(self.curve.features['force_min_curve']['index']))
            dict_param['data_subtract'] = dict_param['data_subtract'][0].drop(
                list_range)
        else:
            dict_param['data_subtract'] = dict_param['data_subtract'][0]
        force_data_pull_copy.update(
            force_data_pull_copy - dict_param['data_subtract'])

        self.ydata_press = force_data_press_copy
        self.ydata_pull = force_data_pull_copy
        ax3.plot(self.time_data_press, force_data_press_copy)
        #ax3.plot(self.time_data_press[index_contact_point__exp_press], force_data_press_copy[index_contact_point__exp_press], marker='D', color='cyan')
        ax3.plot(self.time_data_press[dict_param['index_contact_point_press']],
                 force_data_press_copy[dict_param['index_contact_point_press']], marker='D', color='brown', label='contact point')
        ax3.plot(self.time_data_press[dict_param['list_ind_correction'][0]],
                 force_data_press_copy[dict_param['list_ind_correction'][0]], marker='o', color='#08CC0A', label="first point intreval")
        ax3.plot(self.time_data_press[dict_param['list_ind_correction'][1]],
                 force_data_press_copy[dict_param['list_ind_correction'][1]], marker='o', color='red', label="last point intreval")
        ax3.legend(loc='lower left')

        ax4.plot(self.time_data_pull, force_data_pull_copy)
        #ax4.plot(self.time_data_pull[index_contact_point_exp_pull], force_data_pull_copy[index_contact_point_exp_pull], marker='D', color='cyan')
        ax4.plot(self.time_data_pull[dict_param['index_contact_point_pull']],
                 force_data_pull_copy[dict_param['index_contact_point_pull']], marker='D', color='brown', label='contact point')
        ax4.plot(self.time_data_pull[dict_param['list_index'][0]], force_data_pull_copy[dict_param['list_index']
                 [0]], marker='o', color='red', label="first point intreval")
        ax4.plot(self.time_data_pull[dict_param['list_index'][-1]], force_data_pull_copy[dict_param['list_index']
                 [-1]], marker='o', color='#08CC0A', label='last point intreval')
        ax4.legend(loc='lower right')

        fig.subplots_adjust(wspace=0.3, hspace=0.5)
        fig.tight_layout()

    def accept_correction(self):
        """
        Action of the interface button for accepting the correction after viewing and modifying the data to be displayed in the main interface
        """
        self.segment_press.corrected_data[self.curve.features['main_axis']
                                          ['axe'] + 'Signal1'] = self.ydata_press
        self.segment_pull.corrected_data[self.curve.features['main_axis']
                                         ['axe'] + 'Signal1'] = self.ydata_pull

    def cancel_correction(self, fig):
        """
        cancellation of the correction of the optical effect

        fig: object
            the figure to be modified for the visualization of the modification
        """
        print("cancel")
        list_ind_correction = [87, 1394]
        self.correction_optical_effect(list_ind_correction, fig)
        self.accept_correction()
