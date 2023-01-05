![Python 3.8.5](https://img.shields.io/badge/Python-3.8.5-blue.svg)
![PyQt 5.15.0](https://img.shields.io/badge/PyQt-5.15.0-green.svg)
![License GPL](https://img.shields.io/badge/GNU-GPL3-red.svg)

OT_Analysis
==========

# Tool for managing the results of optical tweezers

OT_Analysis is a tool for extracting, analyzing and classifying data from optical tweezer experiments. In the actual state, it uses forces curves created by a Bruker/JPK Nanowizard II optical tweezers setup.

# Journal Open Source Software

For better visibility and recognition of the real significant contribution in the analysis of optical tweezers data,
the tool was proposed as publication (under review) in the Journal of Open Source Software (https://joss.theoj.org/)


# Installation

## Install Conda/MiniConda && Create conda environment

For an optimal ease of use, we recommend to install conda and create a virtual environment to avoid library conflicts before you install OT_Analyis.

For Linux or Mac

```sh
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
conda create -n "newenv"
conda activate newenv
source .bashrc
conda activate newenv
conda install pip
```

For Windows:

Download conda at this address depending on your OS version: https://docs.conda.io/en/latest/miniconda.html
Go to the conda prompt

```
conda create -n "newenv"
conda activate "newenv"
conda install pip
```

## Install the package from PyPi

For all OSes:

```
python -m pip install OT-Analysis
```

## Launch the software

In order to open the OTAnalysis GUI, in a termnial, run (from anywhere):

```
otanalysis
```

### Build and run from source

You can also download the package on Github and create an already complete virtual environment to launch the software

```
git clone https://github.com/phpuech/OT-Analysis.git
cd OTAnalysis
conda env create -f environment.yml

python -m main

```

# Quick start using OTAnalysis

## 1. Launch the software GUI by typing `otanalysis` in a terminal

## 2. Check and adjust the relevant parameters for the analysis in the first GUI window

## Condition of the experiment

- condition: name of the antibody present on the beads during the experiment, or any other keyword that can be used for latter data processing
- drug: name of the drug used for the analysis,  if present, or any other keyword that can be used for latter data processing

## Fitting management

First, one has to select the curve files to be analyzed, either by selecting a directory or with the multiple selection of files

Then, the analysis choices that will be applied to all of them are selected : 

- model: corresponds to the physical model used to fit the "Press" curves (at the moment, only linear spring or sphere ie. Hertz-like model)
Note that if the sphere model is selected, the physical parameters menu for the calculation of the Young's modulus will appear, with suitable default values that can be user refined
- eta: Poisson's ratio
- bead radius: radius of the bead used during the experiment (in µm)

### Management of curve anomalies

A first step will automatically detect if curves can be processed, following user set parameters. As such, some curves will be either "Incomplete" (no analysis is possible) or "Misaligned" (analysis runs but with a warning)

- curves not having the right number of segments will be discarded since they do not contain any relevant information and correspond mainly to a stopped data collection by the user
- pulling length min : sets the minimum percentage of the length of the "Pull" segment to determine if the curve is rejected despite the presence of all the segments indicated in the header. This corresponds to a curve that has been stopped during the acquisition by the user, but late in the experiment.
- Fmax epsilon: since the trap is a 3D spring, if the bead and cell are misaligned, some force can "bleed-through" the main, experimental, motion axis to the others, which may complexify the data analysis. This parameter corresponds to the percentage of max force tolerated on the major axis (eg. x) to determine misalignment of the curve on the two secondary axes (eg. y, z).

### Classification conditions

The pulling part of the curve contains information about adhesion of the bead to the cell and the eventual pulling of membrane tubes. The present software allows to classify the valid curves (see above) as non adhesive (NAD), adhesive (AD) and tube pulling ones (TU). Moreover, if the tube is not ruptured at the end of the pulling segment, the information is registred for further use.

Some thresholds have to be set to allow this classification :

- NAD if jump is lower than X (in pN): force condition to classify non-adhesive curves
- AD if position is lower than X (in nm): distance condition to separate the membership from the tubes
- AD if slope is lower than X (in pts): condition number of points to separate the membership of the tubes
- Factor overcome noise (x STD): Number of times the standard deviation for the calculation of the characteristic points

Note that due to the curvature of the cells we used (T cells, 10µm in diameter), some optical artifact may appear when the bead (here 1-2µm) comes close to them. This is observed ad a deformation of the baseline to positive or negative forces just before the contact of the two surfaces. To detect it, before giving the hand to the user to correct it if wanted, we set another threshold.

- Factor optical effect (x STD): Number of times the standard deviation to correct the optical effect. 

To ease the reuse of previously used analysis parameters, method saving/loading buttons are avalaible.

## Menu after launching the analysis

There are three options to run the analysis

- Supervised: The computer pre-analyses the data, presents the analysis on graphs and offers to the user a selection of tools to correct, reanalyse, requalify the data. This will happen in a new dedicated window.
- Unsupervised: The computer does it all alone, and you retrieve the output file of the automatic analysis. You cannot act on the analysis.
- ...with graphs: Same as above, but output the graphs of the analysed curves for further consultation

If one chooses supervised, it will open a new window with : 

### Graphic display window with supervision

This allows the visualization of all curves as a function of time on the 3 axes and as a function of distance on the main_axis. Time can be switched to distance.

### Supervision menu

This menu contains a series of buttons and options that are briefly described below.

- Close supervision Panel: Closes the menu for a larger space for visualization of the curves
- Buttons to navigate between the curves. Can be operated with the left/right arrow keys
- Button to save the output file with an indication that the supervision is stopped at this curve (treat_supervised column)
- Curve name is presented
- Zooming for setting characteristic point and fit on distance curves (Pull and Press segment only)
- Curve misaligned warning of misalignment axis, with the possibility to change this status
- Indication of the validity of the fit of the Press segment
- Management of the optical correction with a post-analysis control
- Indication of the validity of the fit of the Pull segment
- Type of curve obtained by automatic classification (type defined checked) that can be hand modified by the user
- Pagination to determine our position in the whole analysis. Possibility to move with the 'Enter' key and the number of the curve

### Changes in characteristic points and zones of fits

In the supervision interface, one can modify the characteristic points and curve fits:
- Go to the force vs distance curve
- In the menu press Edit/Pick event
- in the secondary window that appears choose what you want to modify and click on OK
- then click on the graph, either:
    - on the selected point
    - on the two extreme points for the fit

### Summary plot

When the last curve of the set is reached, a yellow button appears at the bottom of the supervision table that allows the display of a graphic summary window, allowing a rapid examen, by eye, that may help the user to validate the parameters of the analysis.

Note that a toggle button in the upper right corner allows to switch from piecharts to scatter plots for these representations, allowing to see how the parameters of the analysis affect the data.


# Documentation

If you are considering to add any functionality with docstring, update the documentation

## Update

```
make html
```

## Visualization documentation

Click on the Help button in the interface or use (here with firefow, but any browser will do)

```
firefox https://phpuech.github.io/user_doc.html
```

## Output file format

The output data is contained in a `csv` file with 48 columns and 1 line per analyzed curve.
Bellow is the rapid description of each column ; content should appear to the user trivial in the choices of naming. 

Note : this description will soon be made more clear for a non-familiar user.


### Important data from the analysis for post-processing

- treat_supervised type=bool
    True if curve is visualized otherwise False
- automatic_type type=str
    type of curve event determined by the automatic analysis (NAd, AD, TU for non adhesive, adhesive, tube resp.)
- type type=str
    modified type given to the curve using the supervision menu. If there is no supervision then the value is the same as the 'automatic_type' column.
- automatic_AL type=str
    x,y,z alignement of the curves. The value is "No" if the curve is misaligned according to the automatic threshold.
- AL: str
    x,y,z alignement of the curves : readjustment through supervision. If no supervision, then the value is the same as "automatic_AL"
- automatic_AL_axe type=list
    secondary axis along which misalignment occurs, and its sign to know the direction of the misalignment with respect to the direction of the main axis (see below for the conventions for the signs)
- optical_state type=str
    status of the correction for the optical artifact (No_correction, Auto_correction, Manual_correction)


### Analysis parameters saved for data post processing

The following are setting some of the parameters for the analysis

- model type=str
    model for the fit on "Press" segment chosen by the user for the analysis
- tolerance type=float
    noise tolerance for the baseline (as x STD of baseline)

The following one identify the experiments and can be used to pool them for stats or plotting
    
- Date type=str
    date of creation of the curve file (day of the experiment)
- Hour type=str
    time of creation of the curve file (time of the experiment)
    
The following identify the conditions of the experiments
    
- condition type=str
    condition applied to the analysis set (ex : antibodies decorating the bead)
- drug type=str
    name of drug that is used to perturb the system, if used (can be used to add a second condition, ex : surface treatment for cell attachment)
    
The following ones can be used for pooling the data per bead, per cell, per couple...

- bead type=str
    number of the bead used during measurements
- cell type=str
    number of the cell used during measurements
- couple type=str
    couple bead number and cell number, as an identifier

### Data coming from the OT GUI and present in the headers of the files

They represent desired or theoretical values, or positional data recovered from motion angles present in the headers (see JPK OT documentation)

- main_axis type=str
    main axis of the experiment and the direction of approach of the cell with respect to the bead which is here is immobile, at the center of the trapping zone, for the sake of simplicity and fidelity of the measurements. 
    
Here are our choices for orientations and signs.
        +X : the cell approaches from the right
        -X : the cell approaches from the left
        +Y : the cell comes from the top
        -Y : the cell comes from the bottom
        
        
- stiffness type=float
    value of the spring stiffness (calibrated by the software prior to experiment) to correct the distance values
- theorical_contact_force (N) type=float
    theoretical contact force between the beadand the cell required by the user before starting the experiment, from baseline
- theorical_distance_Press (m) type=float
    theoretical maximal length of the "Press" segment. It won't be reached if the stop condition is made to be the max force.
- theorical_speed_Press (m/s) type=float
    theoretical speed of the "Press" segment
- theorical_freq_Press (Hz) type=float
    measurement frequency of the "Press" segment
- time_segment_pause_Wait1 (s) type=float
    pause time of the "Wait" segment (can be 0s if no waiting time is set)
- theorical_distance_Pull (m) type=float
    theoretical length of the "Pull" segment. This max distance will be reached and will mark the end of the curve, even if the cell and bead are not fully detached (see infinite tubes)
- theorical_speed_Pull (m/s) type=float
    theoretical speed of the "Pull" segment
- theorical_freq_Pull (Hz) type=float
    measurement frequency of the "Pull" segment


### Data calculated during the analysis

Note : some of the points which are detected and stored in the following variables can be seen on the documentation images.

- baseline_origin_press (N) type=float
    average of the first 1000 points of the "Press" segment on the data, without correction
- baseline_corrected_press (pN) type=float
    average of the first 1000 points of the "Press" segment on the data corrected to bring the baseline centered on 0, which should then be close to zero
- std_origin_press (N) type=float
    standard deviation of the first 1000 points to define the noise rate of the curve (on the data without correction)
- std_corrected_press (pN) type=float
    standard deviation of the first 1000 points to define the noise rate of the curve (on the data correction). Should be the same as above.
- slope (pN/nm) type=float
    calculation of the force slope in the contact zone for the "Press" segment
- error (pN/nm) type=float
    calculates the error of the force slope for the "Press" segment
- contact_point_index type=int
    index of the contact point between the beadand the cell on the "Press" segment
- contact_point_value  (pN) type=float
    force value of the contact point between the beadand the cell on the "Press" segment
- force_min_press_index type=int
    index of the minimum force of the "Press" segment
- force_min_press_value (pN) type=float
    value of the minimum force of the "Press" segment
- force_min_curve_index type=int
    index of the minimum force of the curve (sometimes confused with minimum Press)
- force_min_curve_value (pN) type=float
    value of the minimum force of the curve (sometimes confused with minimum Press)
- point_release_index type=int
    'index of the point where the cell loses contact with the bead(without taking \ into account the adhesive molecules or the membrane tubes).'
- point_release_value (pN) type=float
    value of the point where the cell loses contact with the bead(without taking \ into account the adhesive molecules or the membrane tubes).
- force_max_pull_index type=int
    index of the maximum force on a part of the "Pull" segment between the release \ point and the return to the baseline
- force_max_pull_value (pN) type=float
    value of the maximum force on a part of the "Pull" segment between the release \ point and the return to the baseline
- force_max_curve_index type=int
    index of the maximum force of the curve
- force_max_curve_value (pN) type=float
    value of the maximum force of the curve
- Pente (pN/nm) type=float
    coefficient of the contact loss slope between the beadand the cell due to the retraction effect of the cell with respect to the ball

### Data calculated if the type of curves is measured to be different from rejected, non-adhesive or infinite tube

Note 1 : an infinite tube is a detected event which has the characteristics of a tube, but still exists when the max pulling length is reached. In short, the final force is not back to the original baseline, which is the case for a non adhesion, an adhesion or a tube of "finite" lenght (lenght < max pulling lenght).

Note 2 : some of the points which are detected and stored in the following variables can be seen on the documentation images.

![Image](./pictures/description_points.png)
- point_transition_index type=int
    index of the break point of the tube (called transition point)
- point_transition_value (pN) type=float
    value of the break point of the tube (called transition point)
- point_return_endline_index type=int
    index of the point where the curve returns to the baseline values
- point_return_endline_value type=float
    value of the point where the curve returns to the baseline values

**Jumps:**
- jump_force_start_pull (pN) type=float
    force jump between the release point and the maximum force of the curve in the case of an adhesion or a finished tube
- jump_force_end_pull (pN) type=float
    force jump between the maximum force of the curve and the point of return to the baseline
- jump_nb_points type=int
    number of points between the point of return to the baseline and the maximum strength of the curve
- jump_time_start_pull (s) type=float
    time between the release point and the maximum force of the curve
- jump_time_end_pull (s) type=float
    time between the maximum force of the curve and the point of return to the baseline
- jump_distance_start_pull (nm) type=float
    distance between the release point and the maximum force of the curve
- jump_distance_end_pull (nm) type=float
    distance between the maximum force of the curve and the point of return to the baseline

### Slope of fits for classification
![Image](./pictures/description_fits.png)
- slope_fitted_classification_max type=float
     slope of the linear adjustment of 1/3 of the points between the release point and the max point removed at the index of the max point
- slope_fitted_classification_release type=float 
    slope of the linear adjustment of 1/3 of the points between the release point and the max point add to the index of the release point
- slope_fitted_classification_max_transition type=float 
    slope of the linear fit between the max point and the transition point
- slope_fitted_classification_return_endline type=float
    slope of the linear fit between the transition point and the baseline return point

### Boolean corresponding to the validation of the fits
- valid_fit_press type=bool
    validation of the fit on the "Press" segment. False by default.

- valid_fit_pull type=bool
    validation of the fit on the "Pull" segment. False by default.


## Adding features

For the ones who could be intersting in extending our code : to add a feature, two options are possible: 
- During the automatic analysis (add your own data extraction procedure)
- After analysis for post processing (add your own data visualisation of statistical analysis)

### In the code

One needs to add a method to the curve object, then call it in the "analyzed_curve" method of the curve object.

This method is called by the controller when the automatic analysis is launched, which is the basis for supervised or not methods.

### In the interface

If one wants to call an external post processing script: 
 - first,  create a method in the controller that loops on the dict_curve (dictionnare of curved object)
 - second,  adapt our add script so that it includes the data of the object
 - third, create a widget in the interface that calls the method of the view's controller attribute

if one wants to add a new feature after analysis but on the object *curve :
 - add a method to the curve object
 - create a widget that calls this method through the dict-curve of the controller

## Adapt input to other raw data formats (eg. other tweezers acquisitions or set-ups)
 
 The input text file must have a global header, a calibration part, segment headers and data, which for us is set by the JPK Instrument / Bruker standarts.
![Image](./pictures/structure_file_text.png)
 
 In short, to adapt to different input, one has to either rewrite the I/O part of the code, or write a converter that modifies the input to fit the present I/O.
 
 If the data do not have a force (xsignal1, ysignal1, zsignal1), time (seriesTime) and distance column:
 
- one will have to implement methods in the specific curve object of your data
- then modify the start of the analysis in the controller in the "create_dict_curves" method
- and finally, adapt the supervision to the data to display


## Future developments

* We noted on some computers issues with the "pick event" function of matplotlib, without finding the origin of the bug or any easy solutions to fix that for the moment. Note that this won't prevent the use of the main functionnalities of the present software.

