#!/usr/bin/python
# -*- coding: utf-8 -*-
# @author Thierry GALLIANO
# @contributors Pierre-Henri PUECH, Laurent LIMOZIN, Guillaume GAY
"""
JPK archive extractor for comprehensive processing of optical tweezer curves
"""
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from struct import unpack_from

################################################################################################################################
################################################################################################################################


class JPKSegment:
    """
    Class to hold data and parameters of a single segment in a JPK archive.
    It is usually created internally when handling a JPK archive with the JPKFile class.
    """

    def __init__(self, shared_properties=None):
        """
        Constructor

        :parameters:
            shared_properties:  
                this parameter needs to hold the dictionary containing the header's contents. Otherwise it is None.
        """
        #: Dictionary holding parameters read from segment header.
        self.parameters = {}
        self.header = {}
        #: Dictionary assigning numpy arrays containing data and definitions on how
        #: to convert raw data to physical data to all channels present in this segment.
        self.data = {}
        self.index = None
        self.shared_properties = shared_properties
    
    ################################################################################################################

    def get_array(self, channels=None, decode=True):
        """
        Constructs a numpy array containing data of given channels. If `decode` is True (default),
        data is converted following conversions defined in segment's header (or shared header).

        :parameters:
             channels:
              List of channels (channel names, i.e. strings) of which to return data.

            decode: bool
                Determines whether data is to be decoded, i.e. transformed according to transformation parameters defined in header files.

        :return: 
            Tuple with two items: 
            (1) Numpy array with labeled columns, one column per requested channel; 
            (2) dictionary assigning units to channels.
        """
        if channels is None:
            channels = []
        _data = {}
        dtypes = []
        # dimension(13 565, 1)pour le premier segment
        shape = self.data[channels[0]][0].shape
        units = {}
        for c in channels:
            if c == 't':
                d = self.data['t'][0]
                unit = 's'
            elif c == 'distance':
                d = self.data['distance'][0]
                unit = 'm/s'
            elif decode:
                d, unit = self.get_decoded_data(c)
            else:
                d, unit = (self.data[c][0], 'digital')
            if d.shape[0] != shape[0]:
                msg = "ERROR! Number of points in data channel '%s'" % c
                msg += "does not match expected number of %i\n" % shape[0]
                raise RuntimeError(msg)
        return d

    ####################################################################################################

    def get_decoded_data(self, channel, conversions_to_be_applied='auto'):
        """
        Get decoded data of one channel. 'decoded' here means the raw, digital data 
        gets converted (to physical data) following certain conversion steps. These steps
        should be defined in the JPK archive's header files. This routine tries to 
        read those conversion steps from those header files by default 
        (`conversions_to_be_applied='auto'`). Alternatively, you can pass a list of
        conversion keywords as `conversions_to_be_applied` manually

        :parameters: 
            channel: str
                Name of channel to convert data of.

            conversions_to_be_applied: str
                Specifying what conversions to apply, see description above.

        :return: 
            Tuple with 2 items; 
                (1) Single-column numpy array containing converted data; 
                (2) Unit as read for last conversion step from header file.
        """
        # NOT COMPLETE, CURRENTLY NOT USED!
        # Idea: Chain of conversions for different channels to fall back to
        #       if automatic detection of conversion protocols fails, and
        #       if no conversion is manually defined in
        #       function JPKSegment.get_decoded_data.
        DEFAULT_CONVERSION_CHAIN = {'height': ('nominal',),
                                    'vDeflection': ('distance', 'force'),
                                    'hDeflection': (),
                                    'strainGaugeHeight': (),
                                    'error': (),
                                    'xSignal1': ()}
        unit = 'digital'
        encoder_parameters = self.data[channel][1]['encoder_parameters']
        # print(encoder_parameters)
        conversion_parameters = self.data[channel][1]['conversion_parameters']['conversion']
        data = self.data[channel][0]

        raw = data[:]
        # Independet of `conversions_to_be_applied`, the first step of conversion
        # apparently has to be as defined by encoder parameters.
        if encoder_parameters:
            if encoder_parameters['scaling']['style'] == 'offsetmultiplier':
                multiplier_raw = float(
                    encoder_parameters['scaling']['multiplier'])
                offset_raw = float(encoder_parameters['scaling']['offset'])
                raw = multiplier_raw * raw + offset_raw

                unit = encoder_parameters['scaling']['unit']['unit']
            else:
                msg = "ERROR! Can only handle converters of type 'offsetmultiplier' so far."
                raise RuntimeError(msg)

        # else:
        #     warnings.warn("No encoder parameters found for channel '{}'.".format(channel))

        # If conversions_to_be_applied is a string, it should be either 'default' or 'auto'.
        # I recommend always using auto, unless you encounter any problems due to conversion.
        if type(conversions_to_be_applied) == str:
            if conversions_to_be_applied == 'default':
                conversions_to_be_applied = DEFAULT_CONVERSION_CHAIN[channel]
                if len(conversions_to_be_applied) == 0:
                    msg = "You request decoding of a channel for which no default conversion scheme is present.\
                        You can apply a temporary conversion scheme by passing a list or tuple of conversion \
                        key words in the parameter conversions_to_be_applied. When I created this module"
                    print(msg)

            elif conversions_to_be_applied == 'auto':
                conversions_to_be_applied = JPKSegment.determine_conversions_automatically(
                    self.data[channel][1]['conversion_parameters'])
            else:
                msg = "Unknown string '%s' for" % conversions_to_be_applied
                msg += " function JPKFile.get_decoded_data's parameter conversions_to_be_applied.\n"
                msg += "Valid strings: 'auto' and 'default'.\nWill now use 'auto'."
                print(msg)
                conversions_to_be_applied = JPKSegment.determine_conversions_automatically(
                    self.data[channel][1]['conversion_parameters'])

        if conversion_parameters:

            conversion_keys = conversion_parameters.keys()
            for c in conversions_to_be_applied:
                if c not in conversion_keys:
                    msg = "Requested conversion '{}' can't be applied,' "
                    msg += "\nno parameters for '{}' found in jpk header."
                    raise RuntimeError(msg.format(c, c))
                else:
                    if conversion_parameters[c]['defined'] == 'false':
                        msg = "Requested conversion '%s' can't be applied!\n" % c
                        msg += "This conversion was specified as not defined\nin jpk header file."
                        raise RuntimeError(msg)

            # if debug:
            #     print("=" * 70)
            #     print("APPLYING CONVERSIONS")
            for c in conversions_to_be_applied:
                # if debug:
                #     print(c)
                if conversion_parameters[c]['scaling']['style'] == 'offsetmultiplier':

                    multiplier = float(
                        conversion_parameters[c]['scaling']['multiplier'])
                    offset = float(
                        conversion_parameters[c]['scaling']['offset'])
                    raw = raw * multiplier + offset

                    unit = conversion_parameters[c]['scaling']['unit']['unit']

                else:
                    msg = "ERROR! Can only handle converters of type 'offsetmultiplier' so far."
                    raise RuntimeError(msg)
        else:
            print("No conversion parameters found for channel '{}'.".format(channel))

        return raw, unit

    ################################################################################################################

    @staticmethod
    def determine_conversions_automatically(conversion_set_dictionary):
        """
        Takes all parameters on how to convert some channel's data read from a header file 
        to determine the chain of conversion steps automatically.

        :parameters:
            conversion_set_dictionary: dict 
                Dictionary of 'conversion-set parameters as parsed from header file with function `parse_header_file`.

        :return: list
            List of conversion keywords.
        """

        # Conversions is a list that will hold the conversion keywords.
        # When populating this list in the following while loop, the
        # order of conversions needs to be reversed. The list is
        # initiated in the following line with the last conversion step's
        # keyword as first item.
        conversions = [conversion_set_dictionary['conversions']['default']]
        # This is the name of the first conversion to be applied (usually
        # from digital back to the analogue potential in voltage).
        raw_name = conversion_set_dictionary['conversions']['base']

        # This list should contain keywords of all conversions necessary to
        # go from first conversion (`raw_name`) to last (first item in `conversions`)
        chain_complete = False
        if conversions[0] == raw_name:
            chain_complete = True
            conversions = []
        while not chain_complete:
            key = conversions[-1]
            previous_conversion = conversion_set_dictionary['conversion'][key]['base-calibration-slot']
            if previous_conversion == raw_name:
                # Completion is reached when the name of the preceding converion
                # matches that of the first converion.
                chain_complete = True
            else:
                conversions.append(previous_conversion)
        conversions.reverse()
        return conversions

#####################################################################################################################################
#####################################################################################################################################


class JPKFile:
    """
    Class to unzip a JPK archive and handle access to its headers and data.

    """

    def __init__(self, compressed_repository):
        """
        Initializes JPKFile object.
        
        :parameters: 
            compressed_repository: str
                Filename of archive to read data from.
        """
        self.jpk_zip = ZipFile(compressed_repository)
        self.data = None
        #: Dictionary containing parameters read from the top level
        #: ``header.properties`` file.
        self.parameters = {}
        self.headers = {}
        self.headers['title'] = compressed_repository.__str__().split(
            "/")[-1].replace(".jpk-nt-force", "")
        #: Number of segments in archive.
        self.num_segments = 0
        #: Dictionary containing one JPKSegment instance per segment.
        self.segments = []
        #: ``None`` if no shared header is present, dictionary containing parameters otherwise.
        self.shared_parameters = None

        # create list of file names in archive (strings, not only file handles).
        list_of_filenames = self.jpk_zip.namelist()

        self.read_files(list_of_filenames)

    #################################################################################################################

    def read_files(self, list_of_filenames):
        """
        Crawls through list of files in archive and processes them automatically
        by name and extension.
        Allows you to fill in the attributes of the JPKFile object:
        self.parameters
        self.headers["header_global"]
        self.segments

        :parameters:
            list_of_filenames: list
                list of files in the archive to browse
        """
        # top header should also be present and the first file in the filelist.
        top_header = list_of_filenames.pop(
            list_of_filenames.index('header.properties'))
        top_header_f = self.jpk_zip.open(top_header)
        top_header_content = top_header_f.readlines()
        top_header_content = JPKFile.decode_binary_strings(top_header_content)

        # parse content of top header file to self.parameters.
        self.parameters, self.headers["header_global"] = JPKFile.parse_header_file(
            top_header_content, "header")
        # if shared header is present ...
        if list_of_filenames.count("shared-data/header.properties"):
            self.parse_shared_header(list_of_filenames)
        # The remaining files should be structured in segments.
        # The loop is checking for every file in which segment folder it is, and
        # whether it's a segment header or data file.
        # For each new segment folder it encounters, a JPKSegment object is created
        # and added to the self.segments dictionary.
        # The JPKSegment is then populated by contents of the segment's
        # header and data files.
        segment = None
        for fname in list_of_filenames:
            split = fname.split("/")
            if split[0] == "segments":
                if len(split) >= 3:
                    # `split[1]` should be the segment's number.
                    segment_number = int(split[1])
                    if segment_number > self.num_segments - 1:
                        new_jpksegment = JPKSegment(self.shared_parameters)
                        new_jpksegment.index = segment_number
                        segment = new_jpksegment
                        self.segments.append(segment)
                        self.num_segments += 1
                    if len(split) == 3 and split[2] == "segment-header.properties":
                        self.read_segment_header(segment, fname)
                    # .dat is the extension for data files.
                    elif len(split) == 4 and split[3][-4:] == ".dat":
                        self.read_segment_data(segment, split, fname)
            # else:
            #     msg = "Encountered new folder '%s'.\n" % split[0]
            #     msg += "Do not know how to handle that."
            #     warnings.warn(msg)

    #####################################################################################################

    @staticmethod
    def decode_binary_strings(list_of_binary_strings):
        """
        Permet de décoder en utf-8 le contenu du header

        :parameters:
            list_of_binary_strings: str
                header content
            
        :return:
            list_line_header: list
                return a list of header lines readable for manipulation
        """
        list_line_header = []
        for line_binaire in list_of_binary_strings:
            list_line_header.append(line_binaire.strip().decode("utf-8"))
        return list_line_header

    #####################################################################################################

    @staticmethod
    def parse_header_file(content, choice_parse=None):
        """
        transform the header list into a dictionary for a faster access to the elements

        :parameters:
            content: list
                list of decoded header lines
            choice_parse: str
                name of the header to be parsed
        
        :return:
            header_dict: dict
                multi-layer dictionary for faster access to data conversion
            header: dict
                single layer dictionary for future transformation into Curve object
        """
        header_dict = {}
        header = {}
        start = 0
        t = ''
        if str(content[start][:2]) == "##":
            start = 1

        datestr = content[start][1:].strip()
        # try:
        #     fmt = '%a %b %d %H:%M:%S %Z %Y'
        #     t = datetime.strptime(datestr, fmt)
        # except:
        #     fmt = '%Y-%m-%d %H:%M:%S %Z%z'
        #     t = datetime.strptime(datestr, fmt)
        if t == '':
            t = datestr

        header_dict['date'] = t
        for line in content[start + 1:]:
            key_header = ""
            key, value = str(line).split('=')
            if choice_parse == "header":
                if len(key.split('.')) > 3:
                    key_header = key.split('header')[1].replace(
                        ".force-settings", "settings")
                elif len(key.split('.')) > 2:
                    key_header = key.replace("force-scan-series.", "")
            elif choice_parse == "shared":
                key_header = key.replace("lcd-info.", "")
            elif choice_parse == "segment":
                if key.startswith("force-segment-header.environment"):
                    key_header = key.replace(
                        "force-segment-header.environment.", "")
                elif key.startswith("force-segment-header"):
                    key_header = key.replace("force-segment-header", "")
                    if key_header.startswith(".settings.segment-settings."):
                        key_header = key_header.replace(".settings.", "")
                elif key.startswith("channel"):
                    key_header = key.replace("channel.", "")
            value = value.strip()
            split_key = key.split(".")
            d = header_dict
            if len(split_key) > 1:
                for s in split_key[:-1]:
                    if s in d:
                        d = d[s]
                    else:
                        d[s] = {}
                        d = d[s]
            d[split_key[-1]] = value
            if value != '':
                header[key_header] = value
        return header_dict, header

    ####################################################################################################

    def parse_shared_header(self, list_of_filenames):
        """
        parsing of the conversion and calibration file included in the archive

        :parameters:
            list_of_filenames: list
                list of files in the archive
        """
        # ... set this to True,
        self.shared_parameters = {}
        # and remove it from list of files.
        shared_header = list_of_filenames.pop(
            list_of_filenames.index("shared-data/header.properties")
        )
        shared_header_f = self.jpk_zip.open(shared_header)
        shared_header_content = shared_header_f.readlines()
        shared_header_content = JPKFile.decode_binary_strings(
            shared_header_content)
        # Parse header content to dictionary.
        self.shared_parameters, self.headers["shared"] = JPKFile.parse_header_file(
            shared_header_content, "shared")
        # print(self.shared_parameters)
        nb_features = int(self.headers["shared"]['lcd-infos.count'])-1
        calibrations = {}
        for k, v in self.headers["shared"].items():
            for index_feature in range(0, nb_features, 1):
                name_feature = self.headers["shared"][str(
                    index_feature) + '.channel.name']
                if k == str(index_feature) + '.conversion-set.conversion.distance.scaling.multiplier':
                    k = name_feature + '_sensitivity'
                    calibrations[k] = v
                if k == str(index_feature) + '.conversion-set.conversion.force.scaling.multiplier':
                    k = name_feature + '_stiffness'
                    calibrations[k] = v
        self.headers['calibrations'] = calibrations

    #####################################################################################################

    def read_segment_header(self, segment, fname):
        """
        Decodes and parses the header files of the different segments of the archive. 
        Allows to set up the "Time" and "Distance" columns of the curve

        :parameters:
            segment: object
                object JPK Segment created
            fname: str(file)
                header file to decode and parse
        """
        header_f = self.jpk_zip.open(fname)
        header_content = header_f.readlines()
        header_content = JPKFile.decode_binary_strings(header_content)
        segment.parameters, segment.header = JPKFile.parse_header_file(
            header_content, "segment")
        num_points = int(
            segment.parameters['force-segment-header']['num-points'])
        t_end = float(segment.parameters['force-segment-header']['duration'])
        t_step = t_end / num_points
        # segment.data['t'] = (np.arange(0.0, t_end, t_step), {'unit': 's'})
        segment.data['t'] = (np.linspace(
            0.0, t_end, num_points, dtype=float), {'unit': 's'})
        if segment.parameters['force-segment-header']['settings']['style'] == 'motion':
            distance_start = 0
            distance_step = 0
            if 'distance' in segment.parameters['channel']:
                distance_start = float(
                    segment.parameters['channel']['distance']['data']['start'])
                distance_step = float(
                    segment.parameters['channel']['distance']['data']['step'])
                distance_end = distance_start + distance_step * num_points
                segment.data['distance'] = (np.linspace(
                    distance_start, distance_end, num_points, dtype=float), {'unit': 'm'})
            else:
                length = float(
                    segment.parameters['force-segment-header']['settings']['segment-settings']['length'])
                duration = float(
                    segment.parameters['force-segment-header']['settings']['segment-settings']['duration'])
                speed = length/duration
                distance = []
                for time in segment.data['t'][0]:
                    if segment.index != 0:
                        segment_previous = self.segments[segment.index - 1]
                        last_distance = segment_previous.data['distance'][0][len(
                            segment_previous.data['distance'][0])-1]
                        distance.append(last_distance - speed*time)
                    else:
                        distance.append(speed*time)
                segment.data['distance'] = (np.array(distance), {'unit': 'm'})
        else:
            distance_stable = 0.0
            if 'distance' in segment.parameters['channel']:
                distance_stable = float(
                    segment.parameters['channel']['distance']['data']['value'])
            else:
                if segment.index != 0:
                    segment_previous = self.segments[segment.index - 1]
                    distance_stable = segment_previous.data['distance'][0][len(
                        segment_previous.data['distance'][0])-1]
            list_distance_pause = np.full((num_points, 1), distance_stable)
            segment.data['distance'] = (list_distance_pause, {'unit': 'm'})
        if self != None:
            links = []
            JPKFile.find_links_in_local_parameters(links,
                                                   segment.parameters,
                                                   self.shared_parameters.keys(), [])
            JPKFile.replace_links(links, segment.parameters,
                                  self.shared_parameters)

    ##########################################################################################################################

    def read_segment_data(self, segment, split, fname):
        """
        decodes the encrypted data in hexadecimal for each column of the segment dataframe

        :parameters:
            segment:object
                object JPK Segment created
            split: str
                name of the column thanks to the name of the file
            fname: str
                file to analyze and decode
        """
        channel_label = split[3][:-4]
        data_f = self.jpk_zip.open(fname)
        content = data_f.read()
        # if debug:
        #     print(segment_number, channel_label)
        # if no shared header was present, this should work
        if self.shared_parameters == None:
            dtype = segment.parameters['channel'][channel_label]['data']['type']
        # otherwise, the chain of keywords is a bit different:
        else:
            # print(segment.parameters['channel'])
            dtype = segment.parameters['channel'][channel_label]['type']
        encoder_parameters = None
        if self.shared_parameters == None:
            if 'data' in segment.parameters['channel'][channel_label]:
                if 'encoder' in segment.parameters['channel'][channel_label]['data']:
                    encoder_parameters = segment.parameters['channel'][channel_label]['data']['encoder']
        else:
            if 'encoder' in segment.parameters['channel'][channel_label]:
                encoder_parameters = segment.parameters['channel'][channel_label]['encoder']

        conversion_parameters = None
        if 'conversion-set' in segment.parameters['channel'][channel_label]:
            if 'conversion' in segment.parameters['channel'][channel_label]['conversion-set']:
                conversion_parameters = segment.parameters['channel'][channel_label]['conversion-set']
        # if not encoder_parameters:
        #     warnings.warn("Did not find encoder parameters for channel {}!".format(split[3][:-4]))
        # if not conversion_parameters:
        #     warnings.warn("Did not find conversion parameters for channel {}!".format(split[3][:-4]))
        num_points = int(
            segment.parameters['force-segment-header']['num-points'])

        data = JPKFile.extract_data(content, dtype, num_points)
        # Transformation en dictionnaire avec les paramètres d'encodage
        segment.data[channel_label] = (data, {'encoder_parameters': encoder_parameters,
                                              'conversion_parameters': conversion_parameters})

    ############################################################################################################################
    @staticmethod
    def extract_data(content, dtype, num_points):
        """
        Converts data from contents of .dat files in the JPKArchive to
        python-understandable formats.
        This function requires the binary `content`, the `dtype` of the 
        binary content as read from the appropiate header file, and the
        number of points as specified in the header file to double check
        the conversion.

        :parameters:
            content: str
                Binary content of a .dat file.
            dtype: str
                Data type as read from heade file.
            num_points: int
                Expected number of points encoded in binary content.
        :return: 
            data: list
                Numpy array containing digital (non-physical, unconverted) data."""
        #: Dictionary assigning item length (in .dat files) and struckt.unpack abbreviation
        #: to the keys used in header files (.properties).
        data_types = {'short': (2, 'h'),
                      'short-data': (2, 'h'),
                      'unsignedshort': (2, 'H'),
                      'integer-data': (4, 'i'),
                      'signedinteger': (4, 'i'),
                      'float-data': (4, 'f')}
        point_length, type_code = data_types[dtype]

        n_entries = len(content) // point_length
        if num_points != n_entries:
            msg = "ERROR! Number of extracted data points is %i," % n_entries
            msg += " and does not match the number of present data points %i" % num_points
            msg += " as read from the segment's header file."
            raise RuntimeError(msg)

        
        data = np.array(unpack_from(f'!{num_points}{type_code}', content))# data decoding
        data = data[:, np.newaxis]  # Transformation from list to matrix
        return data
        

    ###########################################################################################################

    @staticmethod
    def find_links_in_local_parameters(list_of_all_links, parameter_subset, link_keys, chain):
        """
        Allows to find the link between the segment header and the "shared" calibration file

        :parameters:
            list_of_all_links: list
                list with links, it is filled by recursion
            parameter_subset: dict
                segment header dictionary
            link_keys: list
                keys to the shared dictionary
            chain: list
                list of occurrences (links)
        """
        for key in parameter_subset:
            copy_chain = chain[:]
            copy_chain.append(key)
            if key in link_keys and key != "date":
                # print('################## ', key)
                list_of_all_links.append(copy_chain)

            else:
                if isinstance(parameter_subset[key], dict):
                    JPKFile.find_links_in_local_parameters(
                        list_of_all_links, parameter_subset[key], link_keys, copy_chain)
            # print(list_of_all_links)

    #############################################################################################################

    @staticmethod
    def replace_links(links, local_parameters, shared_parameters):
        """
        Allows you to retrieve the channel number corresponding to the associated column to include it in the "shared" 
        directory and associate the information for the conversion.
        Transformation of the "shared" dictionary for data conversion

        :parameters:
            links: list
                list of links retrieved by the find_links_in_local_parameters() function
            local_parameters: dict
                dictionary header segement
            shared_parameters: dict
                "shared" multilayer dictionary

        """
        for chain in links:
            d = local_parameters
            for key in chain[:-1]:
                d = d[key]
            # if debug:
            #     print(("keys_before = ", d.keys()))
            index = d.pop(chain[-1])['*']
            JPKFile.merge(d, shared_parameters[chain[-1]][index])
            # if debug:
            #     print(("keys_shared = ", shared_parameters[chain[-1]][index].keys()))
            #     print(("keys_after = ", d.keys()))

    #############################################################################################################

    @staticmethod
    def merge(a, b, chain=None):
        """
        Allows to merge dictionaries according to their keys and according to the type of their values

        :parameters:
            a: dict
               dictionary 1
            b: dict
                dictionary 2 

        """
        if chain is None:
            chain = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    JPKFile.merge(a[key], b[key], chain + [str(key)])
                elif a[key] == b[key]:
                    pass
                else:
                    raise Exception("Conflict at %s" %
                                    '.'.join(chain + [str(key)]))
            else:
                a[key] = b[key]


if __name__ == "__main__":
    PATH_FILE = Path("../data_test/jpk_nt_force/")
    FILE = PATH_FILE / "b3c3-2021.06.07-14.50.58.217.jpk-nt-force"

    JPK = JPKFile(FILE)
