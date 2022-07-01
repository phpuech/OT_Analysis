#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
Class Controller
"""
import logging
import traceback
from os import sep
from pathlib import Path
import argparse
from shutil import copy
from time import time
from datetime import datetime
import re
from math import ceil, floor
import pandas as pd
import numpy as np
from math import isclose
from pandas.core.tools.numeric import to_numeric
from matplotlib.figure import Figure
from matplotlib import gridspec
import matplotlib.pyplot as plt
from ..__init__ import DATA_DIR
from ..model.curve import Curve
from ..model.segment_curve import Segment
from ..extractor.jpk_extractor import JPKFile



class Controller:
    """
    Instantiates "controller" objects for processing optical curves
    """

    def __init__(self, view=None, path_files=None):
        """
        initialization of the basic attributes of the control

        :parameters:
            view: Object
                interface object
            path_files: str
                path of the folder containing the curves to be analyzed
        """
        # self.tracker = SummaryTracker()
        self.view = view
        self.files = []
        self.dict_curve = {}
        self.check_length_files = True
        self.output = pd.DataFrame(dtype='float64')
        if path_files is not None:
            self.manage_list_files(path_files)
        # methods = {'threshold_align': 30, 'pulling_length': 50, 'model': 'linear',
        #            'eta': 0.5, 'bead_radius': 1, 'factor_noise': 5, 'jump_force': 5,
        #            'jump_point': 200, 'jump_distance': 200, 'drug': 'NaN', 'condition':
        #            'NaN', 'optical': None}
        # self.create_dict_curves(methods)

    ##############################################################################################

    def set_view(self, view):
        """
        setter of the view attribute

        :parameters:
            view: Object
                interface object
        """
        self.view = view
    ################################################################################################

    def manage_list_files(self, path):
        """
        management of the number of files given as input. 
        If greater than 1000 no supervision

        :parameters:
            path: str
                path of the directory to be processed recursively
        """
        dict_files = {}
        length_list_files = 0
        dict_files = self.create_list_files(path, dict_files)
        for list_files in dict_files.values():
            length_list_files += len(list_files)
        if length_list_files > 1000:
            self.check_length_files = False
        for list_files in dict_files.values():
            if self.check_length_files:
                for file in list_files:
                    self.files.append(file)
            else:
                self.files.append(list_files)

    ################################################################################################

    def create_list_files(self, path, dict_files):
        """
        Creation of a file list based on a given directory

        :parameters:
            path: str
                path to a study folder
        """
        path_repository_study = Path(path)
        # Allows you to retrieve all the file names of the directory and store them in a list
        if path_repository_study.is_dir():
            for element in path_repository_study.iterdir():
                if element.is_file():
                    file = element.__str__()
                    name_file = file.split(sep)[-1]
                    dir_file = file.split(sep)[-2]
                    regex = re.match("^b[1-9]+c[1-9]+[a-z]{0,2}-", name_file)
                    if regex:
                        if dir_file in dict_files:
                            dict_files[dir_file].append(file)
                        else:
                            dict_files[dir_file] = [file]
                elif element.is_dir():
                    self.create_list_files(element, dict_files)
        else:
            file = path_repository_study.__str__()
            name_file = file.split(sep)[-1]
            dir_file = file.split(sep)[-2]
            regex = re.match("^b[1-9]+c[1-9]+[a-z]{0,2}-", name_file)
            if regex:
                dict_files[dir_file] = [file]
        return dict_files

    ##############################################################################################

    def create_dict_curves(self, methods, list_files=None):
        """
        creation of the curve list according to the file extension and its conformity

        :parameters:
            methods: dict
                Set of parameters to enter in the interface to launch the analysis
        """
        if self.view is not None:
            if self.view.check_logger:
                self.logger = logging.getLogger('logger_otanalysis.controller')
        self.dict_type_files = {'txt': 0, 'jpk': 0,
                                'NC': 0, 'PB': 0, 'INC': 0, 'DP': 0}
        # 'txt': fichier .txt, 'jpk':fichier .jpk-nt-force,
        # 'NC': not in conformity, 'PB': problematic
        # 'INC': Incomplete, 'DP': Duplicate
        self.list_file_imcomplete = set()
        files = None
        nb = "0/0"
        if list_files is None:
            files = self.files
        else:
            files = list_files
       
        for index_file in range(0, len(files), 1):
            new_curve = None
            type_file = files[index_file].split('.')[-1]
            name_file = files[index_file].split(sep)[-1]
            regex = re.match("^b[1-9]+c[1-9]+[a-z]{0,2}-", name_file)
            name_file = name_file.split('-')
            name_file = str(name_file[0][0:4]) + '-' + '-'.join(name_file[1:])
            nb = str(index_file+1) + "/" + str(len(files))
            print(
                '\n===============================================================================')
            print(files[index_file].split(sep)[-1])
            print(
                '===============================================================================')
            filename = name_file.split('.')[0:-1]
            filename = '.'.join(filename)
            if filename not in self.dict_curve:
                check_incomplete = False
                try:
                    if type_file == 'txt' and regex:
                        new_curve, check_incomplete = Controller.open_file(
                            files[index_file], name_file, methods['threshold_align'],
                            methods['pulling_length'])
                        if not check_incomplete:
                            self.dict_type_files['txt'] += 1
                    elif type_file == 'jpk-nt-force' and regex:
                        new_curve, check_incomplete = Controller.create_object_curve(
                            files[index_file], name_file, methods['threshold_align'],
                            methods['pulling_length'])
                        if not check_incomplete:
                            self.dict_type_files['jpk'] += 1
                    else:
                        print('non-conforming file.')
                        self.dict_type_files['NC'] += 1
                except Exception as error:
                    message = "The file curve is not conform for transformation in curve object"
                    self.problematic_curve(
                        files[index_file], type_file, message, error)
                    self.dict_type_files['PB'] += 1
                if check_incomplete:
                    self.list_file_imcomplete.add(
                        files[index_file].split(sep)[-1])
                    self.dict_type_files['INC'] += 1
                if new_curve is not None:
                    if new_curve.check_incomplete:
                        if type_file == 'jpk-nt-force':
                            type_file = type_file.split('-')[0]
                        Controller.file_incomplete_rejected(
                            type_file, files[index_file])
                        self.dict_type_files['INC'] += 1
                        self.dict_type_files[type_file[0:3]] -= 1
                        self.list_file_imcomplete.add(
                            files[index_file].split(sep)[-1])
                    else:
                        try:
                            error = new_curve.analyzed_curve(
                                methods, False)
                            if self.view is not None:
                                if self.view.check_logger and error is not None:
                                    self.logger.info(
                                        '###########################################')
                                    self.logger.info(
                                        new_curve.file)
                                    self.logger.info(
                                        '###########################################')
                                    self.logger.error(
                                        type(error).__name__)
                                    self.logger.error(error)
                                    self.logger.error(traceback.format_exc())
                                    self.logger.info(
                                        '###########################################\n\n')
                            self.dict_curve[new_curve.file] = new_curve
                            new_curve.features['type'] = new_curve.features['automatic_type']
                            new_curve.features['relative_path'] = files[index_file]
                            new_curve.features['report_problem'] = False
                        except Exception as error:
                            message = "The curve object created but problem \
                                        in analysis due to erroneous data"
                            self.problematic_curve(
                                files[index_file], type_file, message, error)
                            self.dict_type_files['PB'] += 1
            else:
                print('files already processed')
                self.dict_type_files['DP'] += 1
            if self.view is not None:
                self.view.info_processing(nb, len(files))
        

    #############################################################################################

    @ staticmethod
    def open_file(file, name_file, threshold_align, pulling_length=50):
        """
        if file .txt
        Processing of the curve file to create an object
        with all the information necessary for its study

        :parameter:
            file: str
                name of the curve file
            threshold_align: int
                percentage of maximum force for misalignment
        :return:
            new_curve: object
                Curved object with 1 title, 4 dictionaries and 2 dataframes
            check_incomplete: bool
                takes True if the file is incomplete otherwise False
        """
        new_curve = None
        header = {}
        check_incomplete = False
        nb_segments = 0
        dict_segments = {}
        title = name_file.split(sep)[-1].replace(".txt", "")
        file_curve = name_file.split('.')[0:-1]
        file_curve = '.'.join(file_curve)
        check_incomplete = False
        with open(file, 'r') as file_study:
            lines = file_study.read()
            file_study.seek(0)
            header['header_global'] = Controller.parsing_generic(file_study)
            nb_segments = int(header['header_global']
                              ["settings.segments.size"])
            header['calibrations'] = Controller.parsing_generic(file_study)
            check_incomplete = Controller.check_file_incomplete(lines, header['header_global'],
                                                                nb_segments)
            if check_incomplete:
                Controller.file_incomplete_rejected("txt", file)
            else:
                num_segment = 0
                while num_segment < nb_segments:
                    segment = Controller.management_data(file_study, nb_segments,
                                                         num_segment, header['header_global'])
                    if num_segment < nb_segments-1:
                        settings_segment = 'settings.segment.' + \
                            str(num_segment + 1)
                        if header['header_global'][settings_segment + '.style'] != "motion":
                            if float(header['header_global'][settings_segment +
                                                             ".duration"]) == 0.0:
                                num_segment += 1
                    num_segment += 1
                    dict_segments[segment.name] = segment
                new_curve = Curve(file_curve, title, header,
                                  dict_segments, pulling_length)
                dict_align = Controller.alignment_curve(
                    file, new_curve, threshold_align)
                new_curve.features['automatic_AL'] = dict_align
                new_curve.features['AL'] = dict_align['AL']

        return new_curve, check_incomplete

    ################################################################################################

    @ staticmethod
    def create_object_curve(file, name_file, threshold_align, pulling_length=50):
        """
        Creation of the Curve object after extraction of the data from the jpk-nt-force coded file

        :parameters:
            file: str
                path to the jpk-nt-force folder to extract and transform into a Curve python object
            threshold_align: int
                percentage of maximum force for misalignment

        :return:
            new_curve: Object
                returns our curve object ready for analysis and classification
            check_incomplete: bool
                takes True if the file is incomplete otherwise False
        """
        new_curve = None
        new_jpk = JPKFile(file)
        # .replace('.jpk-nt-force', '')
        # file_curve = name_file.__str__().split(sep)[-1]
        file_curve = name_file.split('.')[0:-1]
        file_curve = '.'.join(file_curve)
        check_incomplete = False
        check_incomplete = Controller.file_troncated(new_jpk)
        if check_incomplete:
            Controller.file_incomplete_rejected("jpk", file)
        else:
            columns = []
            dict_segments = {}
            for key in new_jpk.segments[0].data.keys():
                columns.append(key)
            time_end_segment = 0
            time_step = 0
            list_name_segment = ["Press", "Wait", "Pull"]
            num_segment = 0
            for segment in new_jpk.segments:
                name_segment = ""
                dataframe = pd.DataFrame()
                for index_column in range(0, len(columns), 1):
                    if columns[index_column] == 't':
                        data_time = segment.get_array([columns[index_column]])
                        dataframe['time'] = data_time
                        dataframe['seriesTime'] = dataframe['time'].add(time_end_segment
                                                                        + time_step)
                        if segment.index == 0:
                            time_step = dataframe['time'][1]
                        time_end_segment = dataframe['seriesTime'][len(
                            dataframe['seriesTime'])-1]
                    elif columns[index_column] == 'distance':
                        data_distance = segment.get_array(
                            [columns[index_column]])
                        if len(data_distance) != 0:
                            dataframe['distance'] = data_distance
                    else:
                        data_by_column = segment.get_array(
                            [columns[index_column]])
                        dataframe[columns[index_column]] = data_by_column[:, 0]
                if float(new_jpk.headers["header_global"]["settings.segment."
                                                          + str(num_segment) + ".duration"]) == 0.0:
                    num_segment += 1
                if segment.header['segment-settings.style'] == "motion":
                    if num_segment in (0, 1, 2):
                        name_segment = list_name_segment[num_segment]
                    # else:
                    #     name_segment = "Motion_" + str(num_segment)
                else:
                    if num_segment in (0, 1):
                        name_segment = list_name_segment[num_segment]
                    # else:
                    #     name_segment = "Wait_" + str(num_segment)
                num_segment += 1
                dataframe = dataframe.apply(to_numeric)
                new_segment = Segment(segment.header, dataframe, name_segment)
                dict_segments[new_segment.name] = new_segment
            title = new_jpk.headers['title']
            new_curve = Curve(file_curve, title, new_jpk.headers,
                              dict_segments, pulling_length)
            dict_align = Controller.alignment_curve(
                file, new_curve, threshold_align)
            new_curve.features['automatic_AL'] = dict_align
            new_curve.features['AL'] = dict_align['AL']
        return new_curve, check_incomplete

    ###############################################################################################

    def problematic_curve(self, file, extension, message, error):
        """
        function allowing to put in a separate folder the curves having had
        a problem during their analysis

        :parameters:
            file: str
                name of the file to copy
            extension: str
                file extension
            message: str
                message to write in the terminal
            error: object
                error according to the exception raised
        """
        path_dir_problem = ""
        if extension == "jpk":
            path_dir_problem = Path(
                DATA_DIR + sep + 'File_rejected' + sep + 'problem_curve' + sep + 'JPK')
        else:
            path_dir_problem = Path(
                DATA_DIR + sep + 'File_rejected' + sep + 'problem_curve' + sep + 'TXT')
        path_dir_problem.mkdir(parents=True, exist_ok=True)
        copy(file, str(path_dir_problem))
        # print('###########################################')
        # print(type(error).__name__, ':')
        # print(error)
        # print(traceback.format_exc())
        # print(message)
        # print('###########################################')
        if self.view is not None:
            if self.view.check_logger:
                self.logger.info(
                    '###########################################')
                self.logger.info(file)
                self.logger.info(
                    '###########################################')
                self.logger.error(type(error).__name__)
                self.logger.error(error)
                self.logger.error(traceback.format_exc())
                self.logger.info(
                    '###########################################\n\n')

    ############################################################################################

    @ staticmethod
    def file_incomplete_rejected(extension, file):
        """
        Allows you to copy files with incomplete segments to a folder

        ;parameters:
            extension: str
                extension of the curve file (txt or jpk-nt-force)
            file: str
                name of the curve file
        """
        path_dir_incomplete = ""
        if extension == "jpk":
            path_dir_incomplete = Path(
                DATA_DIR + sep + 'File_rejected' + sep + 'Incomplete' + sep + 'JPK')
        else:
            path_dir_incomplete = Path(
                DATA_DIR + sep + 'File_rejected' + sep + 'Incomplete' + sep + 'TXT')
        path_dir_incomplete.mkdir(parents=True, exist_ok=True)
        copy(file, str(path_dir_incomplete))
        print("File incomplete")

    ##############################################################################################
    def show_plot(self, n, abscissa_curve='time'):
        """
        creation of graphs by curves 2 per page maximum

        :parameters:
            n: int
                index of the curve list
            abscissa_curve: str
                name of the data for the abscissa of the curve

        :return:
            fig: Object
                figure to be displayed on the interface canvas
            curve: Object
                the current curve to display graphs

        """
        nb_graph = 1
        list_curves_for_graphs = list(self.dict_curve.values())
        check_distance = False
        if len(list_curves_for_graphs) > 0:
            curve = list_curves_for_graphs[n]
            if 'distance' in curve.dict_segments['Press'].corrected_data:
                check_distance = True
            fig = plt.figure()
            graph_position = 1
            if abscissa_curve == 'time':
                graph_position = self.plot_time(
                    curve, fig, graph_position)
            else:
                for segment in curve.dict_segments.values():
                    if 'distance' in segment.corrected_data:
                        if segment.header_segment['segment-settings.style'] == "motion":
                            if segment.name == 'Press':
                                time_wait = 'Waiting Time: ' + \
                                    curve.parameters_header['header_global']['settings.segment.1.duration'] + ' s'
                                title = segment.name + ' segment, ' + time_wait
                            elif segment.name == 'Pull':
                                title = f"{segment.name} segment"
                            position = int(str(nb_graph) + '2' +
                                           str(graph_position))
                            ax = fig.add_subplot(position, title=title)
                            graph_position = self.plot_distance(
                                curve, segment, ax, graph_position)
                            if segment.name == 'Press':
                                ax.legend(loc="lower left")
                            elif segment.name == 'Pull':
                                handles, labels = ax.get_legend_handles_labels()
                                i = len(labels)-1
                                while i >= 0:
                                    if labels[i] == 'smooth' or labels[i].startswith('fit'):
                                        handles.pop(labels.index(labels[i]))
                                        labels.pop(labels.index(labels[i]))
                                    i -= 1
                                
                                ax.legend(handles, labels, loc="lower right")
                            if self.view.check_legend:
                                ax.get_legend().set_visible(True)
                            else:
                                ax.get_legend().set_visible(False)

        fig.subplots_adjust(wspace=0.3, hspace=0.5)
        fig.tight_layout()
        return fig, curve, check_distance

    ################################################################################################
    def plot_distance(self, curve, segment, ax, graph_position):
        """
        allows the display of graphs as a function of the distance on the 2 segments

        :parameters:
            curve: Object
                curve under analysis
            segment: Object
                segment motion of the curve
            ax: Object
                axis of the figure where to put the graph
            graph_position: int
                position of the graph on the figure

        :return:
            graph_position: int
                back to the following chart positi
        """
        main_axis = curve.features['main_axis']['axe']
        force_data = segment.corrected_data[main_axis + 'Signal1']
        distance_data = segment.corrected_data['distance']
        fitted_data = curve.graphics['fitted_' + segment.name]
        ax.plot(distance_data, force_data, color="#c2a5cf")
        ax.plot(distance_data, fitted_data, color="#5aae61",
                label=curve.features['model'] + " fit")
        # y_smooth = curve.graphics['y_smooth_' + segment.name]
        y_smooth = curve.smooth(
            force_data, self.view.methods['width_window_smooth'], 2)
        ax.plot(distance_data, y_smooth,
                color="#80cdc1", label='smooth')
        index_x_0 = 0
        if segment.name == 'Press':
            threshold_press = curve.graphics['threshold_press']
            threshold_press_neg = np.negative(threshold_press)
            calcul_threshold = curve.features['tolerance'] * \
                curve.graphics['threshold_press'][0] / \
                curve.features['tolerance']
            legend_threshold = f"{curve.features['tolerance']} x STD = +/-{calcul_threshold:.2f}pN"
            ax.plot(distance_data, threshold_press, color='blue',
                    label=legend_threshold, ls='-.', alpha=0.5)
            ax.plot(distance_data, threshold_press_neg,
                    color='blue', alpha=0.5, ls='-.')
            if self.view.methods['optical'] == "Correction" and 'contact_theorical_press' in curve.features:
                index_x_0 = curve.features['contact_theorical_press']['index']
            else:
                index_x_0 = curve.features['contact_point']['index']
            index_max = curve.features["force_min_press"]['index']
            max_curve = curve.features["force_min_curve"]['value']
            ax.plot(distance_data[index_max], force_data[index_max],
                    color='#1b7837', marker='o', ls='None', label='min press')
            ax.plot(distance_data[index_max], max_curve,
                    color='pink', marker='o', label='min curve', ls='None')
            ax.set_ylabel("Force (pN)")
        elif segment.name == 'Pull':
            calcul_threshold = curve.features['tolerance'] * \
                curve.graphics['threshold_pull'][0]/curve.features['tolerance']
            legend_threshold = f"{curve.features['tolerance']} x STD = +/-{calcul_threshold:.2f}pN"
            threshold_pull = curve.graphics['threshold_pull']
            threshold_pull_neg = np.negative(threshold_pull)
            ax.plot(distance_data, threshold_pull, color='blue',
                    label=legend_threshold, ls='-.', alpha=0.5)
            ax.plot(distance_data, threshold_pull_neg,
                    color='blue', alpha=0.5, ls='-.')
            if 'distance_fitted_classification_release' in curve.graphics:
                ax.plot(curve.graphics['distance_fitted_classification_release'],
                        curve.graphics['fitted_classification_release'], label='fit classification release')
            if 'distance_fitted_classification_max' in curve.graphics:
                ax.plot(curve.graphics['distance_fitted_classification_max'],
                        curve.graphics['fitted_classification_max'], label='fit classification max')
            if 'distance_fitted_classification_return_endline' in curve.graphics:
                ax.plot(curve.graphics['distance_fitted_classification_return_endline'],
                        curve.graphics['fitted_classification_return_endline'], label='fit classification return')
            if 'distance_fit_classification_transition' in curve.graphics:
                ax.plot(curve.graphics['distance_fit_classification_transition'],
                        curve.graphics['fit_classification_transition'], label='fit classification transition')
            elif 'distance_fitted_classification_max_transition' in curve.graphics:
                ax.plot(curve.graphics['distance_fitted_classification_max_transition'],
                        curve.graphics['fitted_classification_max_transition'], label='fit classification transition')
            if self.view.methods['optical'] == "Correction":
                index_x_0 = curve.features['contact_theorical_pull']['index']
            else:
                index_x_0 = curve.features['point_release']['index']
            index_max = curve.features['force_max_curve']['index']
            if 'point_return_manual' in curve.features:
                index_return = curve.features['point_return_manual']['index']
                ax.plot(distance_data[index_return], y_smooth[index_return],
                        color='#50441b', marker='P', ls='None', label='point return manual')
            elif curve.features['point_return_endline']['index'] != "NaN":
                index_return = curve.features['point_return_endline']['index']
                ax.plot(distance_data[index_return], y_smooth[index_return],
                        color='#50441b', marker='o', ls='None', label='return')
            if 'point_transition_manual' in curve.features:
                index_transition = curve.features['point_transition_manual']['index']
                ax.plot(distance_data[index_transition], force_data[index_transition],
                        marker='P', ls='None', color='#1E90FF', label='point transition manual')
            elif 'transition_point' in curve.features and curve.features['transition_point']['index'] != 'NaN':
                index_trasition = curve.features['transition_point']['index']
                ax.plot(distance_data[index_trasition], force_data[index_trasition],
                        marker='o', ls='None', color='#1E90FF', label='transition point')
            if 'type' in curve.features:

                if curve.features['type'] != 'NAD' and curve.features['type'] != 'RE':
                    ax.plot(distance_data[index_max], force_data[index_max],
                            color='#1b7837', marker='o', ls='None', label='max')
            else:
                if curve.features['automatic_type'] != 'NAD' \
                        or curve.features['automatic_type'] != 'RE':
                    ax.plot(distance_data[index_max], force_data[index_max],
                            color='#1b7837', marker='o', ls='None', label='max')
        if index_x_0 != 0:
            ax.plot(distance_data[index_x_0], force_data[index_x_0],
                    color='#762a83', marker='o', ls='None', label='contact')

        ax.set_ylim(curve.features['force_min_curve']['value']-2,
                    curve.features['force_max_curve']['value'] + 2)
        ax.set_xlabel("Corrected distance (nm)")
        graph_position += 1

        return graph_position
    #############################################################################################

    def plot_time(self, curve, fig, graph_position):
        """
        allows the display of graphs as a function of time on the 3 axes

        :parameters:
            curve: Object
                curve under analysis
            fig: Object
                figure where to insert the graphics
            graph_position: int
                position of the graph on the figure

        :return:
            graph_position: int
                back to the following chart position
        """
        main_axis = curve.features['main_axis']['axe']
        data_total = curve.retrieve_data_curve('data_corrected')
        segment_pull = curve.dict_segments['Pull']
        force_data_pull = segment_pull.corrected_data[main_axis + 'Signal1']
        time_data_pull = segment_pull.corrected_data['seriesTime']
        threshold_align = curve.graphics['threshold_press'][0]
        threshold_line_pos = np.full(len(data_total), threshold_align)
        threshold_line_neg = np.negative(
            np.full(len(data_total['seriesTime']), threshold_align))
        ax1 = fig.add_subplot(111, title="Main axis: " + main_axis)
        data_total.plot(kind="line", x='seriesTime', y=main_axis + 'Signal1',
                        xlabel='time (s)', ylabel='Force (pN)', ax=ax1, color='green',
                        alpha=0.5, legend=None)
        ax1.plot(data_total['seriesTime'], np.zeros(len(data_total[main_axis + 'Signal1'])),
                 color='green', alpha=0.75)
        ax1.plot(data_total['seriesTime'], threshold_line_pos,
                 color='blue', label='threshold', ls='-.', alpha=0.5)
        ax1.plot(data_total['seriesTime'], threshold_line_neg,
                 color='blue', ls='-.', alpha=0.5)
        index_contact = curve.features['contact_point']['index']
        index_min_press = curve.features['force_min_press']['index']
        index_release = curve.features['point_release']['index']
        index_max = data_total[main_axis + 'Signal1'].argmax()
        if 'point_transition_manual' in curve.features:
            index_transition = curve.features['point_transition_manual']['index']
            ax1.plot(time_data_pull[index_transition], force_data_pull[index_transition],
                     marker='P', ls='None', color='black', label='point transition manual')
        elif 'transition_point' in curve.features and curve.features['transition_point']['index'] != 'NaN':
            index_trasition = curve.features['transition_point']['index']
            ax1.plot(time_data_pull[index_trasition], force_data_pull[index_trasition],
                     marker='o', ls='None', color='#1E90FF', label='transition point')
        if 'point_return_manual' in curve.features:
            index_return_endline = curve.features['point_return_manual']['index']
            ax1.plot(time_data_pull[index_return_endline], force_data_pull[index_return_endline],
                     marker='P', ls='None', color='#50441b', label='point return manual')
        elif curve.features['point_return_endline']['index'] != 'NaN':
            index_return_endline = curve.features['point_return_endline']['index']
            ax1.plot(time_data_pull[index_return_endline], force_data_pull[index_return_endline],
                     marker='o', ls='None', color='#50441b', label='return endline')
        ax1.plot(data_total['time'][index_contact], data_total[main_axis + 'Signal1']
                 [index_contact], marker='o', ls='None', color='#762a83', label='contact point')
        ax1.plot(data_total['time'][index_min_press], data_total[main_axis + 'Signal1']
                 [index_min_press], marker='o', ls='None', color='#8b5847', label='min press')
        ax1.plot(curve.features['time_min_curve']['value (s)'], curve.features['force_min_curve']
                 ['value'], marker='o', ls='None', label='min curve', color='red')
        ax1.plot(time_data_pull[index_release], force_data_pull[index_release],
                 marker='o', ls='None', color='#762a83', label='release point')
        if 'type' in curve.features:
            if curve.features['type'] != 'NAD' and curve.features['type'] != 'RE':
                ax1.plot(data_total['seriesTime'][index_max], data_total[main_axis+'Signal1'][index_max],
                         marker='o', ls='None', color='#1b7837', label='max curve')
        else:
            if curve.features['automatic_type'] != 'NAD' and curve.features['automatic_type'] != 'RE':
                ax1.plot(data_total['seriesTime'][index_max], data_total[main_axis + 'Signal1'][index_max],
                         marker='o', ls='None', color='#1b7837', label='max curve')
        
        ax1.legend(loc="lower left", ncol=2)
        if self.view.check_legend:
            ax1.get_legend().set_visible(True)
        else:
            ax1.get_legend().set_visible(False)
        return graph_position
    #################################################################################################################

    def display_legend(self, fig):
        """
        management of the display of the legend on the graphs thanks to an option in the Edit menu

        :parameters:
            fig: object
                matplotlib figure on which to remove the legend
        """
        for ax in fig.axes:
            if ax.get_legend():
                if not self.view.display_legend.isChecked():
                    ax.get_legend().set_visible(False)
                else:
                    ax.get_legend().set_visible(True)
                self.view.check_legend = ax.get_legend().get_visible()
        fig.canvas.draw_idle()

    ###########################################################################################################################################
    def global_plot(self, n):
        """
        Function allowing the graphical representation of the curves on the different axes
        as a function of time and the main axis on the distance

        :parameters:
            n: int
                index of the curve in the curves dict
        :return:
            fig: object
                the figure to be displayed in the canvas
            curve: object
                the curve associated with the figure
            check_distance: bool
                presence of the distance column in the curve segment data
        """
        # nb_graph = 1
        check_distance = False
        list_curves_for_graphs = list(self.dict_curve.values())
        fig = Figure()
        if len(list_curves_for_graphs) > 0:
            curve = list_curves_for_graphs[n]
            main_axis = curve.features['main_axis']['axe']
            data_total = curve.retrieve_data_curve('data_corrected')
            threshold_align = curve.graphics['threshold alignement']
            threshold_line_pos = np.full(len(data_total), threshold_align)
            threshold_line_neg = np.negative(
                np.full(len(data_total['seriesTime']), threshold_align))
            line_time_min = None
            line_time_max = None

            if 'distance' in data_total:
                gs = gridspec.GridSpec(8, 10)
                line_time_min = 0
                line_time_max = 3
            else:
                gs = gridspec.GridSpec(4, 10)
                line_time_min = 1
                line_time_max = 3

            ax1 = fig.add_subplot(
                gs[line_time_min:line_time_max, 0:4], title="Main axis: " + main_axis)
            # data_total.plot(kind="line", x='seriesTime', y=main_axis + 'Signal1', \
            #     xlabel='time (s)', ylabel='Force (pN)', ax=ax1, color='green', alpha=0.5, legend=None)
            ax1.plot(data_total['seriesTime'], data_total[main_axis +
                     'Signal1'], color='green', alpha=0.5)
            ax1.plot(data_total['seriesTime'], np.zeros(len(data_total[main_axis + 'Signal1'])),
                     color='black', alpha=0.75)
            # ax1.plot(curve.features['time_min_curve']['value (s)'],
            #          curve.features['force_min_curve']['value'], marker='o', label='force_min')
            scale = 0
            if abs(ax1.get_ylim()[0]) < ax1.get_ylim()[1]:
                scale = abs(ax1.get_ylim()[1])
            else:
                scale = abs(ax1.get_ylim()[0])
            ax1.set_xlabel('time (s)')
            ax1.set_ylabel('Force (pN)')
            ax1.set_ylim(-scale - 3, scale + 3)
            # ax1.legend(loc='upper left')
            if main_axis == 'x':
                ax2 = fig.add_subplot(
                    gs[line_time_min:line_time_max, 5:7], title="Axis: y")
                ax2.plot(data_total['seriesTime'], data_total['ySignal1'],
                         color='grey', alpha=0.5)
                ax2.set_xlabel('time (s)')
                ax2.plot(data_total['seriesTime'], np.zeros(len(data_total['ySignal1'])),
                         color='black', alpha=0.75)
                ax2.plot(data_total['seriesTime'], threshold_line_pos,
                         color='blue', ls='-.', alpha=0.5)
                ax2.plot(data_total['seriesTime'], threshold_line_neg,
                         color='blue', ls='-.', alpha=0.5)
                ax2.set_ylim(ax1.get_ylim())
            elif main_axis == 'y':
                ax2 = fig.add_subplot(
                    gs[line_time_min:line_time_max, 5:7], title="Axis: x")
                ax2.plot(data_total['seriesTime'], data_total['xSignal1'],
                         color='grey', alpha=0.5)
                ax2.set_xlabel('time (s)')
                ax2.plot(data_total['seriesTime'], np.zeros(len(data_total['xSignal1'])),
                         color='black', alpha=0.75)
                ax2.plot(data_total['seriesTime'], threshold_line_pos,
                         color='blue', ls='-.', alpha=0.5)
                ax2.plot(data_total['seriesTime'], threshold_line_neg,
                         color='blue', ls='-.', alpha=0.5)
                ax2.set_ylim(ax1.get_ylim())
            ax3 = fig.add_subplot(
                gs[line_time_min:line_time_max, 8:10], title="Axis: z")
            ax3.plot(data_total['seriesTime'], data_total['zSignal1'],
                     color='grey', alpha=0.5)
            ax3.set_xlabel('time (s)')
            ax3.plot(data_total['seriesTime'], np.zeros(len(data_total['zSignal1'])),
                     color='black', alpha=0.75)
            ax3.plot(data_total['seriesTime'], threshold_line_pos,
                     color='blue', ls='-.', alpha=0.5)
            ax3.plot(data_total['seriesTime'], threshold_line_neg,
                     color='blue', ls='-.', alpha=0.5)
            ax3.set_ylim(ax1.get_ylim())
            length = len(curve.dict_segments.values())
            position_start_graph = 0
            num_segment = 0
            for segment in curve.dict_segments.values():
                if 'distance' in segment.corrected_data:
                    check_distance = True
                    if not segment.name.startswith('Wait'):
                        position_end_graph = 0
                        if num_segment == 0:
                            position_end_graph = ceil(
                                position_start_graph + 10/length - 1)
                        else:
                            position_end_graph = 10
                        ax4 = fig.add_subplot(
                            gs[4:8, position_start_graph:position_end_graph])
                        position_start_graph = position_end_graph + 1
                        ax4.plot(
                            segment.corrected_data['distance'], segment.corrected_data[main_axis + 'Signal1'], color="#c2a5cf")
                        ax4.plot(segment.corrected_data['distance'], np.zeros(
                            len(segment.corrected_data[main_axis + 'Signal1'])), color='black', alpha=0.75)
                        ax4.set_xlabel('Corrected distance (nm)')
                    else:
                        position_end_graph = floor(
                            position_start_graph + 10/length - 1)
                        ax4 = fig.add_subplot(
                            gs[4:8, position_start_graph:position_end_graph])
                        ax4.plot(
                            segment.corrected_data['seriesTime'], segment.corrected_data[main_axis + 'Signal1'], color="#34b6cf")
                        position_start_graph = position_end_graph + 1
                        ax4.set_xlabel('time (s)')
                    if segment.name == 'Press':
                        ax4.set_ylabel('Force (pN)')
                    ax4.set_title(segment.name + ' Segment')
                    ax4.set_ylim(curve.features['force_min_curve']['value'] - 1,
                                 curve.features['force_max_curve']['value'] + 2)
                    num_segment += 1
        return fig, curve, check_distance

    ##############################################################################################

    def add_feature(self, name_curve, add_key, add_value):
        """
        Allows to add data to the parameter dictionary of each curve

        :parameters:
            name_curve: str
                file name of the curve
            add_key: str
                key to add in the features
            add_value: struct
                any data structure storing important information
        """
        for curve in self.dict_curve.values():
            if curve.file == name_curve:
                curve.add_feature(add_key, add_value)
            if add_key not in curve.features:
                if add_key == 'type':
                    curve.add_feature(
                        add_key, curve.features['automatic_type'])
                elif add_key in ('valid_fit_press', 'valid_fit_pull'):
                    curve.add_feature(add_key, 'False')
                elif add_key == 'AL':
                    curve.add_feature(add_key, curve.features['AL']['AL'])

    ###########################################################################################################################################
    @ staticmethod
    def save_plot_step(fig, curve, abscissa_curve, directory_graphs):
        """
        recording of step-by-step graphics. Only the one displayed is saved as a png image

        :parameters:
            fig: object
                figure with graphics
            curve: Object
                curve object corresponding to the graphs
            abscissa_curve: str
                name of the data for the abscissa of the curve
        :return:
            name_img: str
                name of the created image

        """
        name_curve = ""
        today = datetime.now().strftime("%d-%m-%Y")
        count = 1
        name_curve = curve.file
        count += 1
        path_graphs = Path(directory_graphs + sep + 'graphs_' + today)
        path_graphs.mkdir(parents=True, exist_ok=True)
        name_img = ""
        if abscissa_curve == 'distance':
            name_img = 'fig_' + name_curve + '_' + today + '_distance.png'
        elif abscissa_curve == 'time':
            name_img = 'fig_' + name_curve + '_' + today + '_time.png'
        else:
            name_img = 'fig_' + name_curve + '_' + today + '_overview.png'
        fig.savefig(path_graphs.__str__() + sep +
                    name_img, bbox_inches='tight')
        fig.close()

    ##############################################################################################

    @ staticmethod
    def parsing_generic(file):
        """
        Functioning to parse the headers of jpk_nt_force text files.

        :parameter:
            file: str
                file to parse
        :return:
            header: dict
                dictionary retrieving all the information from the parsed header
        """
        line = file.readline()
        while not line.startswith("# "):
            line = file.readline()
        header = {}
        while line != '#\n':
            if ": " in line:
                line = line.split(": ")
                if line[1].strip() != '':
                    if line[0].replace("# ", "") not in header:
                        header[line[0].replace("# ", "")] = line[1].strip()
            line = file.readline()
        return header

    ##############################################################################################
    @ staticmethod
    def parsing_data(file, endfile=False):
        """
        Function that parses the data to produce a matrix

        :parameter:
            file: str
                file to parse
            endfile: bool
                boolean to know if we are at the end of the file after this data set
        :return:
            data: matrix
                list of data lists per row of 15 columns
        """
        data = []
        if endfile:
            for line in file:
                line = line.strip().split(" ")
                data.append(line)
        else:
            line = file.readline()
            while line not in ('#\n', '\n'):
                if line != "":
                    line = line.strip().split(" ")
                    data.append(line)
                    line = file.readline()
        return data

    ##############################################################################################
    @ staticmethod
    def management_data(file, nb_segments, num_segment, header_global):
        """
        allows to manage the different cases of segmentation of the curves

        :parameter:
            file: str
                file to process
            nb_segments: int
                number segments in the file
            num_segment: int
                segment number in progress
            header_global: dict
                global information for the curve file
        :return:
            segment: object
                a segment object with 1 header dictionary and 1 dataframe
        """
        name_segment = ""
        list_name_motion = ["Press", "Wait", "Pull"]
        info_segment = Controller.parsing_generic(file)
        table_parameters = Controller.parsing_generic(file)
        if num_segment < nb_segments-1:
            data_segment = Controller.parsing_data(file)
        else:
            data_segment = Controller.parsing_data(file, True)
        settings_segment = 'settings.segment.' + str(num_segment)
        if header_global[settings_segment + '.style'] == "motion":
            name_segment = list_name_motion[num_segment]
        else:
            name_segment = list_name_motion[1] + str(num_segment)
        dataframe = pd.DataFrame(
            data_segment, columns=table_parameters["columns"].split(" "))
        dataframe = dataframe.apply(to_numeric)
        segment = Segment(info_segment, dataframe, name_segment)
        return segment

    #############################################################################################
    @ staticmethod
    def check_file_incomplete(lines, header_global, nb_segments):
        """
        Checks the file, especially if the segments comply
        with the information present in the file header

        :parameters:
            lines: str
                all lines of the file
            header_global: dict
                dictionary of header information
            nb_segments: int
                number of segments stipulated by the header
        :return:
            check_file: bool
                returns true if the file is not truncated
        """
        check_incomplete = True
        nb_block_file = len(lines.split("\n\n"))
        num_segment = 0
        nb_segment_duration_nulle = 0
        for key, value in header_global.items():
            if key == "settings.segment." + str(num_segment) + ".duration":
                if value == "0.0":
                    nb_segment_duration_nulle += 1
                num_segment += 1
        if nb_segments == nb_block_file:
            check_incomplete = False
        elif nb_segments - nb_segment_duration_nulle == nb_block_file:
            check_incomplete = False
        return check_incomplete

    #############################################################################################
    @ staticmethod
    def file_troncated(jpk_object):
        """
        Verification of uninterrupted file during manipulation

        :parameters:
            jpk_object: object
                the object representing the jpk-net-force encryption folder

        :return:
            troncated: bool
                returns true if number of segments not in agreement
                with the initiated one otherwise false
        """
        check_incomplete = False
        expected_nb_segments = int(
            jpk_object.headers['header_global']['settings.segments.size'])
        nb_segments_completed = int(
            jpk_object.headers['header_global']['force-segments.count'])
        nb_segments_pause_null = 0
        if expected_nb_segments != nb_segments_completed:
            for index_segment in range(0, expected_nb_segments-1, 1):
                style = jpk_object.headers['header_global']['settings.segment.'
                                                            + str(index_segment) + '.style']
                if style == 'pause':
                    duration = float(jpk_object.headers['header_global']['settings.segment.'
                                                                         + str(index_segment) + '.duration'])
                    if duration == 0.0:
                        nb_segments_pause_null += 1
            if nb_segments_completed != (expected_nb_segments - nb_segments_pause_null):
                check_incomplete = True
        return check_incomplete

    ############################################################################################

    @ staticmethod
    def alignment_curve(file, new_curve, threshold_align):
        """
        Calls the result of the method of checking the curved object well aligned on the main axis.
        If not then export the file to a rejected directory

        :parameters:
            file: str
                name of the curve file
            new_curve: Object
                curve for the analysis of the alignment
            threshold_align: int
                percentage of maximum force for misalignment
        :return:
            dict_align: dict
                information on the good or bad alignment as well as the secondary axis(es) involved


        """
        dict_align = new_curve.check_alignment_curve(threshold_align)
        if dict_align['AL'] == 'No':
            path_dir_alignment = ""
            name_file = file.split(sep)[-1]
            if name_file.split('.')[-1] == "txt":
                path_dir_alignment = Path(
                    DATA_DIR + sep + 'File_rejected' + sep + 'Alignment' + sep + 'TXT')
            elif name_file.split('.')[-1] == "jpk-nt-force":
                path_dir_alignment = Path(
                    DATA_DIR + sep + 'File_rejected' + sep + 'Alignment' + sep + 'JPK')
            path_dir_alignment.mkdir(parents=True, exist_ok=True)
            copy(file, str(path_dir_alignment))
        return dict_align

    #############################################################################################

    def save_graphs(self, directory_graphs):
        """
        recording of all the graphs of the analysis

        :parameters:
            directory_graphs: str
                path to which to save the graphs
        """
        list_curves_for_graphs = list(self.dict_curve)
        for index_list in range(0, len(list_curves_for_graphs), 1):
            fig, curve, check_distance = self.global_plot(index_list)
            Controller.save_plot_step(fig, curve, 'overview', directory_graphs)
            fig, curve, check_distance = self.show_plot(index_list, 'distance')
            Controller.save_plot_step(fig, curve, 'distance', directory_graphs)
            fig, curve, check_distance = self.show_plot(index_list, 'time')
            Controller.save_plot_step(fig, curve, 'time', directory_graphs)
            nb = str(index_list+1) + "/" + str(len(list_curves_for_graphs))
            self.view.info_processing(nb, len(list_curves_for_graphs))

    ##############################################################################################

    def piechart(self, fig, gs):
        """
        creation of pie charts for the analysis balance window

        :parameters:
            fig: main figure blank to be completed

        :return:
            fig: main figure completed by the different diagrams
        """
        # pie chart incomplete curves
        #gs[line_time_min:line_time_max, 0:4]
        ax_incomplete = fig.add_subplot(gs[0, 0])
        ax_incomplete = self.piechart_incomplete(ax_incomplete)
        title = 'Incomplete \nTotal files: ' + \
            str(len(self.files)) + '\nTotal_files_curve: ' + \
            str(len(self.list_file_imcomplete) + len(self.dict_curve))
        ax_incomplete.set_title(title)

        # piechart auto alignment
        ax_alignment_auto = fig.add_subplot(gs[0, 1])
        ax_alignment_auto, nb_conform_auto = self.piechart_alignment(
            ax_alignment_auto, 'auto')
        ax_alignment_auto.set_title(
            'Automatic Alignment\nTreated curves: ' + str(len(self.dict_curve)))
        # piechart supervised alignment
        ax_alignment_supervised = fig.add_subplot(gs[0, 2])
        ax_alignment_supervised, nb_conform_supervised = self.piechart_alignment(
            ax_alignment_supervised, 'supervised')
        ax_alignment_supervised.set_title(
            'Supervised Alignment\nTreated curves: ' + str(len(self.dict_curve)))

        # piechart optical correction
        ax_correction = fig.add_subplot(gs[1, 0])
        ax_correction = self.piechart_optical_correction(ax_correction)
        ax_correction.set_title(
            'State Correction\nTreated curves: ' + str(len(self.dict_curve)))

        # piechart auto classification
        ax_classification_before = fig.add_subplot(gs[1, 1])
        ax_classification_before = self.piechart_classification(
            ax_classification_before, nb_conform_auto, "automatic_type")
        ax_classification_before.set_title(
            'Classification before\nConforming curves: ' + str(nb_conform_auto))

        # piechart manual classification
        ax_classification_after = fig.add_subplot(gs[1, 2])
        ax_classification_after = self.piechart_classification(
            ax_classification_after, nb_conform_supervised, "type")
        ax_classification_after.set_title(
            'Classification after\nConforming curves: ' + str(nb_conform_supervised))

        return fig
    ###########################################################################################################

    def piechart_alignment(self, ax, name_alignment):
        """
        Creation of the piechart to identify the proportion of misaligned curves 
        compared to those that can be analyzed

        :parameters:
            ax: object
               the axis to modify for piechart display
            name_alignment: str
                management of the alignment before and after supervision

        :return:
            ax: object
                the axis containing the generated piechart
        """
        nb_curves = len(self.dict_curve)
        nb_alignment = 0
        for curve in self.dict_curve.values():
            if name_alignment == 'auto':
                if curve.features['automatic_AL']['AL'] == 'No':
                    nb_alignment += 1
            elif name_alignment == 'supervised':
                if curve.features['AL'] == 'No':
                    nb_alignment += 1
        nb_conforming_curves = nb_curves - nb_alignment
        percent_alignment = nb_alignment/nb_curves * 100
        percent_conforming = nb_conforming_curves/nb_curves * 100
        dict_align_auto = {'AL': f"{percent_alignment:.2f}",
                           'CONF': f"{percent_conforming:.2f}"}
        explode_align = (0.1, 0)
        values_align_auto = [percent_alignment, percent_conforming]
        ax.pie(values_align_auto, explode=explode_align, autopct=lambda pct: self.make_autopct(
            pct, dict_align_auto), shadow=True, startangle=45)
        return ax, nb_conforming_curves

    ######################################################################################################################
    def piechart_incomplete(self, ax):
        """
        Creation of the piechart to determine the proportion of non-compliant 
        or incomplete files compared to the original set

        :parameters:
            ax: object
               the axis to modify for piechart display

        :return:
            ax: object
                the axis containing the generated piechart
        """
        nb_curves = len(self.dict_curve)
        nb_files = len(self.files)
        nb_incomplete = len(self.list_file_imcomplete)
        percent_treat = nb_curves/nb_files * 100
        percent_incomplete = nb_incomplete/nb_files * 100
        percent_no_conforming_files = (
            nb_files-(nb_incomplete + nb_curves))/nb_files * 100

        dict_incomplete = {'INC': f"{percent_incomplete:.2f}",
                           'Treat': f"{percent_treat:.2f}", 'NC': f"{percent_no_conforming_files:.2f}"}
        values = [percent_incomplete, percent_treat,
                  percent_no_conforming_files]
        values_incomplete = [value for value in values if value != 0]
        explode_incomplete = ()
        if len(values_incomplete) == 3:
            explode_incomplete = (0, 0.1, 0)
        elif len(values_incomplete) == 2:
            explode_incomplete = (0, 0.1)
        else:
            explode_incomplete = None
        ax.pie(values_incomplete, explode=explode_incomplete,
               autopct=lambda pct: self.make_autopct(pct, dict_incomplete), shadow=True)

        return ax
    #######################################################################################################################

    def piechart_classification(self, ax, nb_conforming_curves, name_classification):
        """
        Function allowing the creation of classification charts before and after supervision
        This classification is only for well aligned curves and therefore conforms

        :parameters:
            ax: object
               the axis to modify for piechart display
            nb_conforming_curves: int
                Number of curves meeting compliance criteria
            name_classification: str
                name of the classification to be done (before or after supervision) 

        :return:
            ax: object
                the axis containing the generated piechart
        """
        dict_type = {'NAD': 0, 'AD': 0, 'FTU': 0, 'ITU': 0, 'RE': 0}
        for curve in self.dict_curve.values():
            if name_classification == 'automatic_type':
                if curve.features['automatic_AL']['AL'] == 'Yes':
                    if curve.features[name_classification] in dict_type:
                        dict_type[curve.features[name_classification]] += 1
            else:
                if curve.features['AL'] == 'Yes':
                    if curve.features[name_classification] in dict_type:
                        dict_type[curve.features[name_classification]] += 1

        percent_NAD = 0
        percent_AD = 0
        percent_FTU = 0
        percent_ITU = 0
        percent_RE = 0
        if nb_conforming_curves != 0:
            percent_NAD = (
                dict_type['NAD']/nb_conforming_curves * 100)
            percent_AD = (
                dict_type['AD']/nb_conforming_curves * 100)
            percent_FTU = (
                dict_type['FTU']/nb_conforming_curves * 100)
            percent_ITU = (
                dict_type['ITU']/nb_conforming_curves * 100)
            percent_RE = (
                dict_type['RE']/nb_conforming_curves*100)
            dict_classification = {'NAD': f"{percent_NAD:.2f}", 'AD': f"{percent_AD:.2f}",
                                        'FTU': f"{percent_FTU:.2f}", 'ITU': f"{percent_ITU:.2f}", 'RE': f"{percent_RE:.2f}"}
            values = [f"{percent_FTU:.2f}", f"{percent_NAD:.2f}",
                      f"{percent_RE:.2f}", f"{percent_AD:.2f}", f"{percent_ITU:.2f}"]
            values_auto = [value for value in values if value != '0.00']
            ax.pie(values_auto, autopct=lambda pct: self.make_autopct(
                pct, dict_classification), shadow=True, startangle=45)
        return ax

    ####################################################################################################################################
    def piechart_optical_correction(self, ax):
        """
        creation of a pie chart to display the proportion of optical correction according to the chosen mode 
        (None, Auto, Manual)

        :parameters:
            ax: object
                the axis to modify for piechart display

        :return:
            ax: object
                the axis containing the generated piechart
        """
        nb_curves = len(self.dict_curve)
        dict_correction = {'No_correction': 0,
                           'Auto_correction': 0, 'Manual_correction': 0}
        for curve in self.dict_curve.values():
            dict_correction[curve.features['optical_state']] += 1
        percent_no_correction = (
            dict_correction['No_correction']/nb_curves * 100)
        percent_auto_correction = (
            dict_correction['Auto_correction']/nb_curves * 100)
        percent_manual_correction = (
            dict_correction['Manual_correction']/nb_curves * 100)
        dict_correction_percent = {'None': f"{percent_no_correction:.2f}",
                                   'Auto': f"{percent_auto_correction:.2f}", 'Manual': f"{percent_manual_correction:.2f}"}
        values = [percent_no_correction,
                  percent_auto_correction, percent_manual_correction]
        values_correction = [value for value in values if value != 0]
        ax.pie(values_correction, autopct=lambda pct: self.make_autopct(
            pct, dict_correction_percent), shadow=True, startangle=45)
        return ax

    ##################################################################################################################################

    def make_autopct(self, pct, dico):
        """
        management of the labels of the corners of the diagram

        :parameters:
            dico:dictionary of values and labels of the diagram

        :return:
            pct: percentage
            val: label
        """
        retour = None
        try:
            pct = f"{pct:.2f}"
            list_keys = list(dico.keys())
            list_values = list(dico.values())
            num_key = list_values.index(pct)
            val = list_keys[num_key]
            del dico[val]
            retour = None
            if float(pct) < 10:
                retour = f"{pct}%({val})"
            retour = f"{pct}%\n({val})"
        except Exception as error:
            # print('###########################################')
            # print(type(error).__name__, ':')
            # print(error)
            # print(traceback.format_exc())
            # print('value problem')
            # print('###########################################')
            if self.view is not None:
                if self.view.check_logger:
                    self.logger.info(
                        '###########################################')
                    self.logger.error(type(error).__name__)
                    self.logger.error(error)
                    self.logger.error(traceback.format_exc())
                    self.logger.info(
                        '###########################################\n\n')
        if retour != None:
            return retour

    #############################################################################################################################

    def scatter_bilan(self, fig, gs):
        """
        scatter plot for a general verification of the classification results thanks to the characteristic points

        :parameters:
            fig: object
                figure matplotlib to be modified to display scatters instead of piecharts
            gs: object
                grid for the placement of the axes on the figure
        """
        self.check_annot = False
        annotations_ax1 = []
        annotations_ax2 = []
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        color_dict = {'AD': 'red', 'FTU': 'green', 'ITU': 'blue'}
        artist_plot = []
        for curve in self.dict_curve.values():
            if curve.features['type'] in ('AD', 'FTU', 'ITU'):
                text_annot=curve.file + '/page ' + str(list(self.dict_curve.values()).index(curve)+1)
                ax1.plot(curve.features['jump_distance_end_pull (nm)'], curve.features['jump_force_end_pull (pN)'],
                         marker='o', color=color_dict[curve.features['type']], picker=True, label=curve.file)
                annotations_ax1.append(ax1.annotate(text_annot, xy=(curve.features['jump_distance_end_pull (nm)'],
                                                                    curve.features['jump_force_end_pull (pN)']), xytext=(-60, 10),
                                                    textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), visible=False))
                
                if 'slope_fit_classification_transition' in curve.features:
                    ax2.plot(curve.features["slope_fit_classification_transition"],
                                curve.features['jump_force_end_pull (pN)'], marker='o', color=color_dict[curve.features['type']],
                                picker=True, label=curve.file)
                elif 'slope_fitted_classification_max_transition' in curve.features:
                    ax2.plot(curve.features["slope_fitted_classification_max_transition"],
                                curve.features['jump_force_end_pull (pN)'], marker='o', color=color_dict[curve.features['type']],
                                picker=True, label=curve.file)
                annotations_ax2.append(ax2.annotate(text_annot, xy=(curve.features["slope_fitted_classification_max_transition"],
                                                                    curve.features['jump_force_end_pull (pN)']), xytext=(-100, 10),
                                                    textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), visible=False))
                
                # h, l = ax1.get_legend())
                # print(h)
                # print(l)
        # max_xlim = ax2.get_xlim()[1]
        # ax2.set_xlim(-max_xlim, max_xlim)
        ax1.axvline(self.view.methods['jump_distance'], ls='-.')
        ax1.axhline(self.view.methods['jump_force'], ls='-.')
        ax2.axvline(0.025, ls='-.')
        ax2.axvline(-0.025, ls='-.')
        ax1.set_xlabel("jump_distance (nm)")
        ax1.set_ylabel("jump_force (pN)")
        ax2.set_ylabel("jump_force (pN)")
        ax2.set_xlabel("slope_fit_max_return (pN/nm)")
        fig.canvas.mpl_connect("pick_event", lambda event: self.click_curve(
            event, ax1, fig, annotations_ax1, 50, 1))
        fig.canvas.mpl_connect("pick_event", lambda event: self.click_curve(
            event, ax2, fig, annotations_ax2, 0.01, 10))
        fig.subplots_adjust(wspace=0.5)
        pos_x = 0.45
        pos_y = 0.95
        for type, color in color_dict.items():
            fig.text(pos_x, pos_y, u"\u25CF " + type, color=color)
            pos_x += 0.05
        return fig

    #########################################################################################################
    def click_curve(self, event, ax, fig, annotations, tolerance_x, tolerance_y):
        """
        click on the scatters plot to display the name of the corresponding curve

        :parameters:
            event: signal object
                mouse click event
            ax: object
                matplotlib object to work on the chosen axis
            fig: object
                fig matplotlib to refresh the figure at each click
            annotations: list
                list of annotations for each point on the axis
            tolerance_x: float
                tolerance on the x-axis to check that the click is at the position of an existing point
            tolerance_y: float
                idem on the ordinate axis
        """
        check_annot = False
        for point in ax.get_lines():
            if point.get_marker() == 'o':
                for annot in annotations:
                    if event.mouseevent.xdata is not None and event.mouseevent.ydata is not None:
                        if isclose(event.mouseevent.xdata, point.get_xdata(), abs_tol=tolerance_x) and isclose(event.mouseevent.ydata, point.get_ydata(), abs_tol=tolerance_y):
                            if point.get_label() == annot.get_text().split('/')[0]:
                                if not annot.get_visible() and not check_annot:
                                    annot.set_visible(True)
                                    fig.canvas.draw_idle()
                                    check_annot = True
                                else:
                                    annot.set_visible(False)
                                    fig.canvas.draw_idle()

    #########################################################################################################

    def count_cell_bead(self):
        """
        Calculation of the number of cells, beads and couples in each set for the bilan window

        :return:
            nb_beads: int
                number of beads
            nb_cells: int
                number of cells
            nb_couples: int
                number of couples
        """
        dict_beads = {}
        dict_cells = {}
        dict_couple = {}
        for curve in self.dict_curve.values():
            if curve.output['bead'] in dict_beads:
                dict_beads[curve.output['bead']] += 1
            else:
                dict_beads[curve.output['bead']] = 1
            if curve.output['cell'] in dict_cells:
                dict_cells[curve.output['cell']] += 1
            else:
                dict_cells[curve.output['cell']] = 1
            if curve.output['couple'] in dict_couple:
                dict_couple[curve.output['couple']] += 1
            else:
                dict_couple[curve.output['couple']] = 1
        nb_beads = len(dict_beads)
        nb_cells = len(dict_cells)
        nb_couples = len(dict_couple)
        return nb_beads, nb_cells, nb_couples

    ##############################################################################################

    def clear(self):
        """
        Reset of the controller data structure
        """
        self.files = []
        self.dict_curve = {}
        self.test = None
        self.output = pd.DataFrame()

    ##############################################################################################

    def output_save(self, path_directory):
        """
        Transformation of the characteristics of each curve into a general dataframe.
        Writing of this dataframe in a csv file

        :parameters:
            path_directory: str
                name of the folder to save the output
        """
        print("output_save")
        today = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        name_file= ""
        if len(self.dict_curve) > 0:
            dict_infos_curves = {}
            for curve in self.dict_curve.values():
                curve.creation_output_curve()
                dict_infos_curves[curve.file] = curve.output
            self.output = self.output.from_dict(
                dict_infos_curves,  orient='index')
            self.output['main_axis'] = self.output['main_axis_sign'] + \
                self.output['main_axis_axe']
            self.output.drop(
                ['main_axis_sign', 'main_axis_axe'], axis=1, inplace=True)
            if 'valid_fit_press' not in self.output:
                self.output['valid_fit_press'] = False
            if 'valid_fit_pull' not in self.output:
                self.output['valid_fit_pull'] = False
            name_parameters = ""
            error_parameters = ''
            if self.output['model'][0] == 'linear':
                name_parameters = 'slope (pN/nm)'
                error_parameters = 'error (pN/nm)'
            elif self.output['model'][0] == 'sphere':
                name_parameters = 'young (Pa)'
                error_parameters = 'error young (Pa)'
            liste_labels = ['treat_supervised', 'automatic_type', 'type', 'report_problem' ,'automatic_AL', 'AL', 'automatic_AL_axe',
                            'optical_state', 'model', 'Date', 'Hour', 'condition', 'drug', 'tolerance', 'bead', 'cell', 'couple',
                            'main_axis', 'stiffness (N/m)', 'theorical_contact_force (N)', 'theorical_distance_Press (m)',
                            'theorical_speed_Press (m/s)', 'theorical_freq_Press (Hz)', 'theorical_distance_Pull (m)',
                            'theorical_speed_Pull (m/s)', 'theorical_freq_Pull (Hz)', 'baseline_origin_press (N)',
                            'baseline_corrected_press (pN)', 'std_origin_press (N)', 'std_corrected_press (pN)',
                            name_parameters, error_parameters, 'contact_point_index', 'contact_point_value',
                            'force_min_press_index', 'force_min_press_value', 'force_min_curve_index',
                            'force_min_curve_value', 'time_min_curve_index', 'time_min_curve_value (s)',
                            'point_release_index', 'point_release_value', 'force_max_pull_index',
                            'force_max_pull_value', 'force_max_curve_index', 'force_max_curve_value',
                            'transition_point_index', 'transition_point_value (pN)', 'point_return_endline_index',
                            'point_return_endline_value']
            if len(liste_labels) != len(self.output.columns):
                for label in self.output.columns:
                    if label not in liste_labels:
                        if label == 'type':
                            liste_labels.insert(1, label)
                        elif label.startswith('time_segment_pause'):
                            self.output[label] = self.output[label].replace(
                                np.nan, 0)
                            if label.endswith('Wait1 (s)'):
                                liste_labels.insert(liste_labels.index(
                                    'theorical_freq_Press (Hz)') + 1, label)
                            else:
                                liste_labels.insert(liste_labels.index(
                                    'theorical_freq_Pull (Hz)') + 1, label)
                        else:
                            liste_labels.append(label)
            self.output = self.output[liste_labels]

            self.output.rename(columns={'contact_point_value': 'contact_point_value  (pN)', 'force_min_press_value': 'force_min_press_value (pN)',
                                        'force_min_curve_value': 'force_min_curve_value (pN)', 'force_max_curve_value': 'force_max_curve_value (pN)',
                                        'point_release_value': 'point_release_value (pN)', 'force_max_pull_value': 'force_max_pull_value (pN)',
                                        'point_return_endline_value': 'point_return_endline_value (pN)'}, inplace=True)

            for incomplete in self.list_file_imcomplete:
                self.output.loc[incomplete, 'automatic_type'] = 'INC'
                self.output.loc[incomplete, 'type'] = 'INC'
            if self.view is None:
                path_directory = Path("Result")
                path_directory.mkdir(parents=True, exist_ok=True)
                path_directory = path_directory.__str__()
            name_file = path_directory + sep + 'output_' + today + '.csv'
            self.output.to_csv(name_file, sep='\t',
                               encoding='utf-8', na_rep="NaN")
        return name_file

    ##############################################################################################


def parse_args():
    """
    function to add command line arguments to run the controller without GUI

    """
    parser = argparse.ArgumentParser(description="Creation curve objects")
    parser.add_argument("-p", "--path", type=str,
                        help="Name of the folder containing the curves", required=True)
    parser.add_argument(
        "-o", "--output", help="Name of the folder where to save the results", required=True)
    parser.add_argument("-m", "--method", type=argparse.FileType('r'),
                        help="path to a method file (.tsv)", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    START_TIME = time()
    args = parse_args()
    PATH_FILES = args.path
    OUTPUT_DIRECTORY = args.output
    METHOD = args.method
    controller = Controller(None, PATH_FILES)
    controller.create_dict_curves(METHOD)
    controller.output_save(OUTPUT_DIRECTORY)
    print("--- %s seconds ---" % (time() - START_TIME))
