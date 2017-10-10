#!/usr/bin/python 

from copy import deepcopy
import os
import re
import pprint

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"

INI_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini")
INI_DEFAULT_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/PocketNC.ini.default")
CALIBRATION_OVERLAY_FILE = os.path.join(POCKETNC_DIRECTORY, "Settings/CalibrationOverlay.inc")

ConfigHelp = {
    'AXIS_0':{
        '':                 { 'default':'',          'help':'General parameters for the individual components in the axis control module. The axis section names begin numbering at 0, and run through the number of axes specified in the [TRAJ] AXES entry minus 1.' },
        'TYPE':             { 'default':'LINEAR',    'help':'The type of axes, either LINEAR or ANGULAR'},
        'WRAPPED_ROTARY':   { 'default':'1',         'help':'When this is set to 1 for an ANGULAR axis the axis will move 0-359.999 degrees. Positive Numbers will move the axis in a positive direction and negative numbers will move the axis in the negative direction.'},
        'LOCKING_INDEXER':  { 'default':'1',         'help':'When this is set to 1 a G0 move for this axis will initiate an unlock with axis.N.unlock pin then wait for the axis.N.is-unlocked pin then move the axis at the rapid rate for that axis. After the move the axis.N.unlock will be false and motion will wait for axis.N.is-unlocked to go false. Moving with other axes is not allowed when moving a locked rotary axis. '},
        'UNITS':            { 'default':'INCH',      'help':'If specified, this setting overrides the related [TRAJ] UNITS setting. (e.g., [TRAJ]LINEAR_UNITS if the TYPE of this axis is LINEAR, [TRAJ]ANGULAR_UNITS if the TYPE of this axis is ANGULAR) '},
        'MAX_VELOCITY':     { 'default':'1.2',       'help':'Maximum velocity for this axis in machine units per second.'},
        'MAX_ACCELERATION': { 'default':'20.0',      'help':'Maximum acceleration for this axis in machine units per second squared. '},
        'BACKLASH':         { 'default':'0.0000',    'help':'Backlash in machine units. Backlash compensation value can be used to make up for small deficiencies in the hardware used to drive an axis. If backlash is added to an axis and you are using steppers the STEPGEN_MAXACCEL must be increased to 1.5 to 2 times the MAX_ACCELERATION for the axis. '},
        'COMP_FILE':        { 'default':'file.extension',          'help':'A file holding compensation structure for the axis. The file could be named xscrew.comp, for example, for the X axis. File names are case sensitive and can contain letters and/or numbers. The values are triplets per line separated by a space. The first value is nominal (where it should be). The second and third values depend on the setting of COMP_FILE_TYPE. Currently the limit inside LinuxCNC is for 256 triplets per axis. If COMP_FILE is specified, BACKLASH is ignored. Compensation file values are in machine units. '},
        'COMP_FILE_TYPE':   { 'default':'0 or 1',    'help':'If 0: The second and third values specify the forward position (where the axis is while traveling forward) and the reverse position (where the axis is while traveling reverse), positions which correspond to the nominal position.          If 1: The second and third values specify the forward trim (how far from nominal while traveling forward) and the reverse trim (how far from nominal while traveling in reverse), positions which correspond to the nominal position.    Example triplet with COMP_FILE_TYPE = 0: 1.00 1.01 0.99 +    Example triplet with COMP_FILE_TYPE = 1: 1.00 0.01 -0.01'},
        'MIN_LIMIT':        { 'default':'-1000',     'help':'The minimum limit (soft limit) for axis motion, in machine units. When this limit is exceeded, the controller aborts axis motion. '},
        'MAX_LIMIT':        { 'default':'1000',      'help':'The maximum limit (soft limit) for axis motion, in machine units. When this limit is exceeded, the controller aborts axis motion. '},
        'MIN_FERROR':       { 'default':'0.010',     'help':'This is the value in machine units by which the axis is permitted to deviate from commanded position at very low speeds. If MIN_FERROR is smaller than FERROR, the two produce a ramp of error trip points. You could think of this as a graph where one dimension is speed and the other is permitted following error. As speed increases the amount of following error also increases toward the FERROR value. '},
        'FERROR':           { 'default':'1.0',       'help':'FERROR is the maximum allowable following error, in machine units. If the difference between commanded and sensed position exceeds this amount, the controller disables servo calculations, sets all the outputs to 0.0, and disables the amplifiers. If MIN_FERROR is present in the .ini file, velocity-proportional following errors are used. Here, the maximum allowable following error is proportional to the speed, with FERROR applying to the rapid rate set by [TRAJ]MAX_VELOCITY, and proportionally smaller following errors for slower speeds. The maximum allowable following error will always be greater than MIN_FERROR. This prevents small following errors for stationary axes from inadvertently aborting motion. Small following errors will always be present due to vibration, etc. The following polarity values determine how inputs are interpreted and how outputs are applied. They can usually be set via trial-and-error since there are only two possibilities. The LinuxCNC Servo Axis Calibration utility program (in the AXIS interface menu Machine/Calibration and in TkLinuxCNC it is under Setting/Calibration) can be used to set these and more interactively and verify their results so that the proper values can be put in the INI file with a minimum of trouble. '},
        'HOME':             { 'default':'0.0',       'help':'The position that the joint will go to upon completion of the homing sequence'},
        'HOME_OFFSET':      { 'default':'0.0',       'help':'The axis position of the home switch or index pulse, in machine units. When the home point is found during the homing process, this is the position that is assigned to that point. When sharing home and limit switches and using a home sequence that will leave the home/limit switch in the toggled state the home offset can be used define the home switch position to be other than 0 if your HOME position is desired to be 0. '},
        'HOME_SEARCH_VEL':  { 'default':'0.0',       'help':'Initial homing velocity in machine units per second. Sign denotes direction of travel. A value of zero means assume that the current location is the home position for the machine. If your machine has no home switches you will want to leave this value at zero. '},
        'HOME_LATCH_VEL':   { 'default':'0.0',       'help':'Homing velocity in machine units per second to the home switch latch position. Sign denotes direction of travel. '},
        'HOME_FINAL_VEL':   { 'default':'0.0',       'help':'Velocity in machine units per second from home latch position to home position. If left at 0 or not included in the axis rapid velocity is used. Must be a positive number. '},
        'HOME_USE_INDEX':   { 'default':'NO',        'help':'If the encoder used for this axis has an index pulse, and the motion card has provision for this signal you may set it to yes. When it is yes, it will affect the kind of home pattern used. Currently, you cant home to index with steppers unless youre using stepgen in velocity mode and PID.'},
        'HOME_IGNORE_LIMITS': { 'default':'NO',      'help':'When you use the limit switch as a home switch and the limit switch this should be set to YES. When set to YES the limit switch for this axis is ignored when homing. You must configure your homing so that at the end of your home move the home/limit switch is not in the toggled state you will get a limit switch error after the home move. '},
        'HOME_IS_SHARED':   { 'default':'<n>',       'help':'If the home input is shared by more than one axis set <n> to 1 to prevent homing from starting if the one of the shared switches is already closed. Set <n> to 0 to permit homing if a switch is closed. '},
        'HOME_SEQUENCE':    { 'default':'<n>',       'help':'Used to define the "Home All" sequence. <n> starts at 0 and no numbers may be skipped. If left out or set to -1 the joint will not be homed by the "Home All" function. More than one axis can be homed at the same time. '},
        'VOLATILE_HOME':    { 'default':'0',         'help':'When enabled (set to 1) this joint will be unhomed if the Machine Power is off or if E-Stop is on. This is useful if your machine has home switches and does not have position feedback such as a step and direction driven machine. '},
        'DEADBAND':         { 'default':'0.000015',  'help':'Might be used by a PID component and the assumption is that the output is volts.  How close is close enough to consider the motor in position, in machine units. '},
        'BIAS':             { 'default':'0.000',     'help':'Might be used by a PID component and the assumption is that the output is volts.  This is used by hm2-servo and some others. Bias is a constant amount that is added to the output. In most cases it should be left at zero. However, it can sometimes be useful to compensate for offsets in servo amplifiers, or to balance the weight of an object that moves vertically. bias is turned off when the PID loop is disabled, just like all other components of the output.'},
        'P':                { 'default':'50',        'help':'Might be used by a PID/servo component.  The proportional gain for the axis servo. This value multiplies the error between commanded and actual position in machine units, resulting in a contribution to the computed voltage for the motor amplifier. The units on the P gain are volts per machine unit, eg volts/unit'},
        'I':                { 'default':'0',         'help':'Might be used by a PID/servo component.  The integral gain for the axis servo. The value multiplies the cumulative error between commanded and actual position in machine units, resulting in a contribution to the computed voltage for the motor amplifier. The units on the I gain are volts per machine unit second, eg volts/(unit second)'},
        'D':                { 'default':'0',         'help':'Might be used by a PID/servo component.  The derivative gain for the axis servo. The value multiplies the difference between the current and previous errors, resulting in a contribution to the computed voltage for the motor amplifier. The units on the D gain are volts per machine unit per second, e.g. volts/(unit second)'},
        'FF0':              { 'default':'0',         'help':'Might be used by a PID/servo component.  The 0th order feed forward gain. This number is multiplied by the commanded position, resulting in a contribution to the computed voltage for the motor amplifier. The units on the FF0 gain are volts per machine unit'},
        'FF1':              { 'default':'0',         'help':'Might be used by a PID/servo component.  The 1st order feed forward gain. This number is multiplied by the change in commanded position per second, resulting in a contribution to the computed voltage for the motor amplifier. The units on the FF1 gain are volts per machine unit per second'},
        'FF2':              { 'default':'0',         'help':'Might be used by a PID/servo component.  The 2nd order feed forward gain. This number is multiplied by the change in commanded position per second per second, resulting in a contribution to the computed voltage for the motor amplifier. The units on the FF2 gain are volts per machine unit per second per second'},
        'OUTPUT_SCALE':     { 'default':'1.000',     'help':'Might be used by a PID/servo component.  These two values are the scale and offset factors for the axis output to the motor amplifiers. The second value (offset) is subtracted from the computed output (in volts), and divided by the first value (scale factor), before being written to the D/A converters. The units on the scale value are in true volts per DAC output volts. The units on the offset value are in volts. These can be used to linearize a DAC. '},
        'OUTPUT_OFFSET':    { 'default':'0.000',     'help':'Might be used by a PID/servo component.  These two values are the scale and offset factors for the axis output to the motor amplifiers. The second value (offset) is subtracted from the computed output (in volts), and divided by the first value (scale factor), before being written to the D/A converters. The units on the scale value are in true volts per DAC output volts. The units on the offset value are in volts. These can be used to linearize a DAC. '},
        'MAX_OUTPUT':       { 'default':'10',        'help':'Might be used by a PID/servo component.  The maximum value for the output of the PID compensation that is written to the motor amplifier, in volts. The computed output value is clamped to this limit. The limit is applied before scaling to raw output units. The value is applied symmetrically to both the plus and the minus side.'},
        'INPUT_SCALE':      { 'default':'20000',     'help':'Might be used by a PID/servo component.  '},
        'ENCODER_SCALE':    { 'default':'20000',     'help':'Might be used by a PID/servo component.  In PNCconf built configs Specifies the number of pulses that corresponds to a move of one machine unit as set in the [TRAJ] section. For a linear axis one machine unit will be equal to the setting of LINEAR_UNITS. For an angular axis one unit is equal to the setting in ANGULAR_UNITS. A second number, if specified, is ignored. '},
        'SCALE':            { 'default':'4000',      'help':'Might be used by a stepgen component.  Number of output step pulses for one unit of linear travel.'},
        'STEP_SCALE':       { 'default':'4000',      'help':'Might be used by a stepgen component. In PNCconf built configs Specifies the number of pulses that corresponds to a move of one machine unit as set in the [TRAJ] section. For stepper systems, this is the number of step pulses issued per machine unit. For a linear axis one machine unit will be equal to the setting of LINEAR_UNITS. For an angular axis one unit is equal to the setting in ANGULAR_UNITS. For servo systems, this is the number of feedback pulses per machine unit. A second number, if specified, is ignored.'},
        'ENCODER_SCALE':    { 'default':'',          'help':'Might be used by a stepgen component. (Optionally used in PNCconf built configs) - Specifies the number of pulses that corresponds to a move of one machine unit as set in the [TRAJ] section. For a linear axis one machine unit will be equal to the setting of LINEAR_UNITS. For an angular axis one unit is equal to the setting in ANGULAR_UNITS. A second number, if specified, is ignored.'},
        'STEPGEN_MAXACCEL': { 'default':'',          'help':'Might be used by a stepgen component.  Acceleration limit for the step generator. This should be 1% to 10% larger than the axis MAX_ACCELERATION. This value improves the tuning of stepgens "position loop". If you have added backlash compensation to an axis then this should be 1.5 to 2 times greater than MAX_ACCELERATION. '},
        'STEPGEN_MAXVEL':   { 'default':'',          'help':'Might be used by a stepgen component. Older configuration files have a velocity limit for the step generator as well. If specified, it should also be 1% to 10% larger than the axis MAX_VELOCITY. Subsequent testing has shown that use of STEPGEN_MAXVEL does not improve the tuning of stepgens position loop. '}
    },
     'EMC':{
        '':                 { 'default':'',          'help':'General LinuxCNC information'},
        'VERSION':          { 'default':'$Revision$','help':'The version number for the INI file. The default value looks odd because it is automatically updated when using the Revision Control System. Its a good idea to change this number each time you revise your file. If you want to edit this manually just change the number and leave the other tags alone.'},
        'MACHINE':          { 'default':'My Controller', 'help':'This is the name of the controller, which is printed out at the top of most graphical interfaces. You can put whatever you want here as long as you make it a single line long.'},
        'DEBUG':            { 'default':'0',         'help':'Debug level 0 means no messages will be printed when LinuxCNC is run from a terminal. Debug flags are usually only useful to developers. See src/emc/nml_intf/emcglb.h for other settings.'}
    },
    'DISPLAY':{
        '':                 { 'default':'',          'help':'Different user interface programs use different options, and not every option is supported by every user interface. The main two interfaces for LinuxCNC are AXIS and Touchy. Axis is an interface for use with normal computer and monitor, Touchy is for use with touch screens. Descriptions of the interfaces are in the Interfaces section of the User Manual.'},
        'DISPLAY':          { 'default':'axis',      'help':'The name of the user interface to use. Valid options may include: axis, touchy, keystick, mini, tklinuxcnc, xemc.'},
        'POSITION_OFFSET':  { 'default':'RELATIVE',  'help':'The coordinate system (RELATIVE or MACHINE) to show when the user interface starts. The RELATIVE coordinate system reflects the G92 and G5x coordinate offsets currently in effect'},
        'POSITION_FEEDBACK':{ 'default':'ACTUAL',    'help':'The coordinate value (COMMANDED or ACTUAL) to show when the user interface starts. The COMMANDED position is the ideal position requested by LinuxCNC. The ACTUAL position is the feedback position of the motors.'},
        'MAX_FEED_OVERRIDE':{ 'default':'1.2',       'help':'The maximum feed override the user may select. 1.2 means 120% of the programmed feed rate.'},
        'MIN_SPINDLE_OVERRIDE':{ 'default':'0.5',    'help':'The minimum spindle override the user may select. 0.5 means 50% of the programmed spindle speed. (This is useful as its dangerous to run a program with a too low spindle speed). '},
        'MAX_SPINDLE_OVERRIDE':{ 'default':'1.0',    'help':'The maximum spindle override the user may select. 1.0 means 100% of the programmed spindle speed.'},
        'PROGRAM_PREFIX':   { 'default':'~/emc2/nc_files', 'help':'The default location for g-code files and the location for user-defined M-codes. This location is searched for the file name before the subroutine path and user M path if specified in the [RS274NGC] section.'},
        'INTRO_GRAPHIC':    { 'default':'emc2.gif',  'help':'The image shown on the splash screen'},
        'INTRO_TIME':       { 'default':'5',         'help':'The maximum time to show the splash screen, in seconds. '},
        'CYCLE_TIME':       { 'default':'0.05',      'help':'Cycle time in seconds that display will sleep between polls. '},
        'DEFAULT_LINEAR_VELOCITY':{ 'default':'.25', 'help':'Applies to axis display only.  The default velocity for linear jogs, in machine units per second.'},
        'MIN_VELOCITY':     { 'default':'.01',       'help':'Applies to axis display only.  The approximate lowest value the jog slider.'},
        'MAX_LINEAR_VELOCITY':{ 'default':'1.0',     'help':'Applies to axis display only.  The maximum velocity for linear jogs, in machine units per second. '},
        'MIN_LINEAR_VELOCITY':{ 'default':'.01',     'help':'Applies to axis display only.  The approximate lowest value the jog slider. '},
        'DEFAULT_ANGULAR_VELOCITY':{ 'default':'.25','help':'Applies to axis display only.  The default velocity for angular jogs, in machine units per second. '},
        'MIN_ANGULAR_VELOCITY':{ 'default':'.01',    'help':'Applies to axis display only.  The approximate lowest value the jog slider. '},
        'MAX_ANGULAR_VELOCITY':{ 'default':'1.0',    'help':'Applies to axis display only.  The maximum velocity for angular jogs, in machine units per second. '},
        'INCREMENTS':       { 'default':'1 mm, .5 in, ...', 'help':'Applies to axis display only.  Defines the increments available for incremental jogs. The INCREMENTS can be used to override the default. The values can be decimal numbers (e.g., 0.1000) or fractional numbers (e.g., 1/16), optionally followed by a unit (cm, mm, um, inch, in or mil). If a unit is not specified the machine unit is assumed. Metric and imperial distances may be mixed: INCREMENTS = 1 inch, 1 mil, 1 cm, 1 mm, 1 um is a valid entry. '},
        'GRIDS':            { 'default':'10 mm, 1 in, ...',  'help':'Applies to axis display only.  Defines the preset values for grid lines. The value is interpreted the same way as INCREMENTS. '},
        'OPEN_FILE':        { 'default':'/full/path/to/file.ngc', 'help':'Applies to axis display only.  The file to show in the preview plot when AXIS starts. Use a blank string "" and no file will be loaded at start up. '},
        'EDITOR':           { 'default':'gedit',     'help':'Applies to axis display only.  The editor to use when selecting File > Edit to edit the gcode from the AXIS menu. This must be configured for this menu item to work. Another valid entry is gnome-terminal -e vim. '},
        'TOOL_EDITOR':      { 'default':'tooledit',  'help':'Applies to axis display only.  The editor to use when editing the tool table (for example by selecting "File > Edit tool table..." in Axis). Other valid entries are "gedit", "gnome-terminal -e vim", and "gvim".'},
        'PYVCP':            { 'default':'/filename.xml', 'help':'Applies to axis display only.  The PyVCP panel description file. See the PyVCP section for more information. '},
        'LATHE':            { 'default':'1',         'help':'Applies to axis display only.  This displays in lathe mode with a top view and with Radius and Diameter on the DRO. '},
        'GEOMETRY':         { 'default':'XYZABCUVW', 'help':'Applies to axis display only.  Controls the preview and backplot of rotary motion. This item consists of a sequence of axis letters, optionally preceded by a "-" sign. Only axes defined in [TRAJ]AXES should be used. This sequence specifies the order in which the effect of each axis is applied, with a "-" inverting the sense of the rotation. The proper GEOMETRY string depends on the machine configuration and the kinematics used to control it. The example string GEOMETRY=XYZBCUVW is for a 5-axis machine where kinematics causes UVW to move in the coordinate system of the tool and XYZ to move in the coordinate system of the material. The order of the letters is important, because it expresses the order in which the different transformations are applied. For example rotating around C then B is different than rotating around B then C. Geometry has no effect without a rotary axis. '},
        'ARCDIVISION':      { 'default':'64',        'help':'Applies to axis display only.  Set the quality of preview of arcs. Arcs are previewed by dividing them into a number of straight lines; a semicircle is divided into ARCDIVISION parts. Larger values give a more accurate preview, but take longer to load and result in a more sluggish display. Smaller values give a less accurate preview, but take less time to load and may result in a faster display. The default value of 64 means a circle of up to 3 inches will be displayed to within 1 mil (.03%).'},
        'MDI_HISTORY_FILE': { 'default':'',          'help':'Applies to axis display only.  The name of a local MDI history file. If this is not specified Axis will save the MDI history in .axis_mdi_history in the users home directory. This is useful if you have multiple configurations on one computer. '},
        'HELP_FILE':     { 'default':'tklinucnc.txt',       'help':'Applies to TKLinuxCNC display only.  Path to help file.'}
    },
    'FILTER':{
        '':                 { 'default':'',          'help':'AXIS has the ability to send loaded files through a filter program. This filter can do any desired task: Something as simple as making sure the file ends with M2, or something as complicated as detecting whether the input is a depth image, and generating g-code to mill the shape it defines. The [FILTER] section of the ini file controls how filters work. First, for each type of file, write a PROGRAM_EXTENSION line. Then, specify the program to execute for each type of file. This program is given the name of the input file as its first argument, and must write RS274NGC code to standard output. This output is what will be displayed in the text area, previewed in the display area, and executed by LinuxCNC when Run.'},
        'PROGRAM_EXTENSION':{ 'default':'.extension Description', 'help':'Example: The following lines add support for the image-to-gcode converter included with LinuxCNC: PROGRAM_EXTENSION = .png,.gif,.jpg Greyscale Depth Image, then png = image-to-gcode, gif = image-to-gcode, jpg = image-to-gcode'}
    },
    'RS274NGC':{
        '':                 { 'default':'',          'help':''},
        'PARAMETER_FILE':   { 'default':'myfile.var','help':'The file located in the same directory as the ini file which contains the parameters used by the interpreter (saved between runs).'},
        'ORIENT_OFFSET':    { 'default':'0',         'help':'A float value added to the R word parameter of an M19 Orient Spindle operation. Used to define an arbitrary zero position regardless of encoder mount orientation. '},
        'RS274NGC_STARTUP_CODE': { 'default':'G01 G17 G20 G40 G49 G64 P0.001 G80 G90 G92 G94 G97 G98', 'help':'A string of NC codes that the interpreter is initialized with. This is not a substitute for specifying modal g-codes at the top of each ngc file, because the modal codes of machines differ, and may be changed by g-code interpreted earlier in the session. '},
        'SUBROUTINE_PATH':  { 'default':'ncsubroutines:/tmp/testsubs:lathesubs:millsubs', 'help':'Specifies a colon (:) separated list of up to 10 directories to be searched when single-file subroutines are specified in gcode. These directories are searched after searching [DISPLAY]PROGRAM_PREFIX (if it is specified) and before searching [WIZARD]WIZARD_ROOT (if specified). The paths are searched in the order that they are listed. The first matching subroutine file found in the search is used. Directories are specified relative to the current directory for the inifile or as absolute paths. The list must contain no intervening whitespace. '},
        'USER_M_PATH':      { 'default':'myfuncs:/tmp/mcodes:experimentalmcodes', 'help':'Specifies a list of colon (:) separated directories for user defined functions. Directories are specified relative to the current directory for the inifile or as absolute paths. The list must contain no intervening whitespace. '},
        'USER_DEFINED_FUNCTION_MAX_DIRS': { 'default':'5', 'help':'The maximum number of directories defined at compile time'}
    },
    'EMCMOT':{
        '':                 { 'default':'',          'help':'This section is a custom section and is not used by LinuxCNC directly. Most configurations use values from this section to load the motion controller.'},
        'EMCMOT':           { 'default':'motmod',    'help':'The motion controller name is typically used here. '},
        'BASE_PERIOD':      { 'default':'50000',     'help':'The Base task period in nanoseconds.'},
        'SERVO_PERIOD':     { 'default':'1000000',   'help':'This is the "Servo" task period in nanoseconds. '},
        'TRAJ_PERIOD':      { 'default':'100000',    'help':'This is the Trajectory Planner task period in nanoseconds.'}
    },
    'TASK':{
        '':                 { 'default':'',          'help':''},
        'TASK':             { 'default':'milltask',  'help':'Specifies the name of the task executable. The task executable does various things, such as communicate with the UIs over NML, communicate with the realtime motion planner over non-HAL shared memory, and interpret gcode. Currently there is only one task executable that makes sense for 99.9% of users, milltask.'},
        'CYCLE_TIME':       { 'default':'0.010',     'help':'The period, in seconds, at which TASK will run. This parameter affects the polling interval when waiting for motion to complete, when executing a pause instruction, and when accepting a command from a user interface. There is usually no need to change this number.'}
    },
    'HAL':{
        '':                 { 'default':'',          'help':''},
        'TWOPASS':          { 'default':'ON',        'help':'Use two pass processing for loading HAL comps. With TWOPASS processing, all [HAL]HALFILES are first read and multiple appearances of loadrt directives for each module are accumulated. No hal commands are executed in this initial pass. '},
        'HALFILE':          { 'default':'example.hal', 'help':'Execute the file example.hal at start up. If HALFILE is specified multiple times, the files are executed in the order they appear in the ini file. Almost all configurations will have at least one HALFILE, and stepper systems typically have two such files, one which specifies the generic stepper configuration (core_stepper.hal) and one which specifies the machine pin out (xxx_pinout.hal) '},
        'HALCMD':           { 'default':'command',   'help':'Execute command as a single HAL command. If HALCMD is specified multiple times, the commands are executed in the order they appear in the ini file. HALCMD lines are executed after all HALFILE lines. '},
        'SHUTDOWN':         { 'default':'shutdown.hal', 'help':'Execute the file shutdown.hal when LinuxCNC is exiting. Depending on the hardware drivers used, this may make it possible to set outputs to defined values when LinuxCNC is exited normally. However, because there is no guarantee this file will be executed (for instance, in the case of a computer crash) it is not a replacement for a proper physical e-stop chain or other protections against software failure. '},
        'POSTGUI_HALFILE':  { 'default':'example2.hal', 'help':'(Only with the TOUCHY and AXIS GUI) Execute example2.hal after the GUI has created its HAL pins. '},
        'HALUI':            { 'default':'halui',     'help':'Adds the HAL user interface pins. '}
    },
    'HALUI':{
        '':                 { 'default':'',          'help':''},
        'MDI_COMMAND':      { 'default':'G53 G0 X0 Y0 Z0', 'help':' An MDI command can be executed by using halui.mdi-command-00. Increment the number for each command listed in the [HALUI] section. '}
    },
    'TRAJ':{
        '':                 { 'default':'',          'help':'The [TRAJ] section contains general parameters for the trajectory planning module in motion.'},
        'COORDINATES':      { 'default':'X Y Z',     'help':'The names of the axes being controlled. Only X, Y, Z, A, B, C, U, V, W are valid. Only axes named in COORDINATES are accepted in g-code. This has no effect on the mapping from G-code axis names (X- Y- Z-) to joint numbers for trivial kinematics, X is always joint 0, A is always joint 3, and U is always joint 6, and so on. It is permitted to write an axis name twice (e.g., X Y Y Z for a gantry machine) but this has no effect. '},
        'AXES':             { 'default':'3',         'help':'One more than the number of the highest joint number in the system. For an XYZ machine, the joints are numbered 0, 1 and 2; in this case AXES should be 3. For an XYUV machine using trivial kinematics, the V joint is numbered 7 and therefore AXES should be 8. For a machine with nontrivial kinematics (e.g., scarakins) this will generally be the number of controlled joints. '},
        'JOINTS':           { 'default':'3',         'help':'(This config variable is used by the Axis GUI only, not by the trajectory planner in the motion controller.) Specifies the number of joints (motors) in the system. For example, an XYZ machine with a single motor for each axis has 3 joints. A gantry machine with one motor on each of two of the axes, and two motors on the third axis, has 4 joints. '},
        'HOME':             { 'default':'0 0 0',     'help':'Coordinates of the homed position of each axis. Again for a fourth axis you will need 0 0 0 0. This value is only used for machines with nontrivial kinematics. On machines with trivial kinematics this value is ignored. '},
        'LINEAR_UNITS':     { 'default':'<units>',   'help':'Specifies the machine units for linear axes. Possible choices are (in, inch, imperial, metric, mm). This does not affect the linear units in NC code (the G20 and G21 words do this). '},
        'ANGULAR_UNITS':    { 'default':'<units>',   'help':'Specifies the machine units for rotational axes. Possible choices are deg, degree (360 per circle), rad, radian (2pi per circle), grad, or gon (400 per circle). This does not affect the angular units of NC code. In RS274NGC, A-, B- and C- words are always expressed in degrees.'},
        'DEFAULT_VELOCITY': { 'default':'0.0167',    'help':'The initial rate for jogs of linear axes, in machine units per second. The value shown in Axis equals machine units per minute. '},
        'DEFAULT_ACCELERATION': { 'default':'2.0',   'help':'In machines with nontrivial kinematics, the acceleration used for "teleop" (Cartesian space) jogs, in machine units per second per second. '},
        'MAX_VELOCITY':     { 'default':'5.0',       'help':'The maximum velocity for any axis or coordinated move, in machine units per second. The value shown equals 300 units per minute. '},
        'MAX_ACCELERATION': { 'default':'20.0',      'help':'The maximum acceleration for any axis or coordinated axis move, in machine units per second per second. '},
        'POSITION_FILE':    { 'default':'position.txt', 'help':'If set to a non-empty value, the joint positions are stored between runs in this file. This allows the machine to start with the same coordinates it had on shutdown. This assumes there was no movement of the machine while powered off. If unset, joint positions are not stored and will begin at 0 each time LinuxCNC is started. This can help on smaller machines without home switches. '},
        'NO_FORCE_HOMING':  { 'default':'1',          'help':'The default behavior is for LinuxCNC to force the user to home the machine before any MDI command or a program is run. Normally, only jogging is allowed before homing. Setting NO_FORCE_HOMING = 1 allows the user to make MDI moves and run programs without homing the machine first. Interfaces without homing ability will need to have this option set to 1. '}
    },
    'EMCIO':{        
        '':                 { 'default':'',          'help':'Tool changeer related information.'},
        'EMCIO':            { 'default':'io',        'help':'Name of IO controller program, e.g., io'},
        'CYCLE_TIME':       { 'default':'0.100',     'help':'The period, in seconds, at which EMCIO will run. Making it 0.0 or a negative number will tell EMCIO not to sleep at all. There is usually no need to change this number. '},
        'TOOL_TABLE':       { 'default':'tool.tbl',  'help':'The file which contains tool information, described in the User Manual. '},
        'TOOL_CHANGE_POSITION': { 'default':'0 0 2', 'help':'Specifies the XYZ location to move to when performing a tool change if three digits are used. Specifies the XYZABC location when 6 digits are used. Specifies the XYZABCUVW location when 9 digits are used. Tool Changes can be combined. For example if you combine the quill up with change position you can move the Z first then the X and Y. '},
        'TOOL_CHANGE_WITH_SPINDLE_ON': { 'default':'1', 'help':'The spindle will be left on during the tool change when the value is 1. Useful for lathes or machines where the material is in the spindle, not the tool. '},
        'TOOL_CHANGE_QUILL_UP': { 'default':'1',     'help':'The Z axis will be moved to machine zero prior to the tool change when the value is 1. This is the same as issuing a G0 G53 Z0. '},
        'TOOL_CHANGE_AT_G30':   { 'default':'1',     'help':'The machine is moved to reference point defined by parameters 5181-5186 for G30 if the value is 1. For more information on G30 and Parameters see the G Code Manual. '},
        'RANDOM_TOOLCHANGER':   { 'default':'1',     'help':'This is for machines that cannot place the tool back into the pocket it came from. For example, machines that exchange the tool in the active pocket with the tool in the spindle. '}
    }
}
ConfigHelp['AXIS_1'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_2'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_3'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_4'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_5'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_6'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_7'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_8'] = ConfigHelp['AXIS_0'];
ConfigHelp['AXIS_9'] = ConfigHelp['AXIS_0'];


# WARNING - this was copied from Rockhopper/LinuxCNCWebSktSvr.py then modified
# changes to that code, will likely need to be reflected here
# TODO pull this code out into a shared location 
def read_ini_data(ini_file, only_section=None, only_name=None):
    global ConfigHelp

    INIFileData = {
        "parameters":[],
        "sections":{}
    }
   
    sectionRegEx = re.compile( r"^\s*\[\s*(.+?)\s*\]" )
    keyValRegEx = re.compile( r"^\s*(.+?)\s*=\s*(.+?)\s*$" )

    section = 'NONE'
    comments = ''
    idv = 1
    with open( ini_file ) as file_:
        for line in file_:
            if  line.lstrip().find('#') == 0 or line.lstrip().find(';') == 0:
                comments = comments + line[1:]
            else:
                mo = sectionRegEx.search( line )
                if mo:
                    section = mo.group(1)
                    hlp = ''
                    try:
                        if (section in ConfigHelp):
                            hlp = ConfigHelp[section]['']['help'].encode('ascii','replace')
                    except:
                        pass
                    if (only_section is None or only_section == section):
                        INIFileData['sections'][section] = { 'comment':comments, 'help':hlp }
                    comments = '' 
                else:
                    mo = keyValRegEx.search( line )
                    if mo:
                        hlp = ''
                        default = ''
                        try:
                            if (section in ConfigHelp):
                                if (mo.group(1) in ConfigHelp[section]):
                                    hlp = ConfigHelp[section][mo.group(1)]['help'].encode('ascii','replace')
                                    default = ConfigHelp[section][mo.group(1)]['default'].encode('ascii','replace')
                        except:
                            pass

                        if (only_section is None or (only_section == section and only_name == mo.group(1) )):
                            INIFileData['parameters'].append( { 'id':idv, 'values':{ 'section':section, 'name':mo.group(1), 'value':mo.group(2), 'comment':comments, 'help':hlp, 'default':default } } )
                        comments = ''
                        idv = idv + 1
    return INIFileData


def ini_differences(defaults, save):
    diff = {
        'parameters': [],
        'sections': {}
    }
    for param in save['parameters']:
        section = param['values']['section']
        name = param['values']['name']
        value = param['values']['value']

        for default_param in defaults['parameters']:
            if name == default_param['values']['name'] and section == default_param['values']['section'] and value != default_param['values']['value']:
                diff['parameters'].append(param)

    for param in diff['parameters']:
        diff['sections'][param['values']['section']] = save['sections'][param['values']['section']]

    return diff

def merge_ini_data(defaults, overlay):
    merged = deepcopy(defaults)

    for param in overlay['parameters']:
        section = param['values']['section']
        name = param['values']['name']
        value = param['values']['value']

        for default_param in merged['parameters']:
            if name == default_param['values']['name'] and section == default_param['values']['section']:
                print "Setting [%s](%s) to %s" % (section, name, value)
                default_param['values']['value'] = value

    return merged

def write_ini_data(ini_data, ini_file):
    print "Writing INI file..."
    # construct the section list
    sections = {}
    sections_sorted = []
    for line in ini_data['parameters']:
        sections[line['values']['section']] = line['values']['section']
    for section in sections:
        sections_sorted.append( section )
    sections_sorted = sorted(sections_sorted)

    inifile = open(ini_file, 'w', 1)

    for section in sections_sorted:
        # write out the comments before the section header
        if (section in ini_data['sections']):
            commentlines = ini_data['sections'][section]['comment'].split('\n')
            for c_line in commentlines:
                if len(c_line) > 0:
                    inifile.write( '#' + c_line + '\n' )

        #write the section header
        inifile.write( '[' + section + ']\n' )

        #write the key/value pairs
        for line in ini_data['parameters']:
            if line['values']['section'] == section :
                if (len(line['values']['comment']) > 0):
                    commentlines = line['values']['comment'].split('\n')
                    for c_line in commentlines:
                        if len(c_line) > 0:
                            inifile.write( '#' + c_line +'\n' )
                if (len(line['values']['name']) > 0):
                    inifile.write( line['values']['name'] + '=' + line['values']['value'] + '\n' )
        inifile.write('\n\n')
    inifile.close()

if __name__ == "__main__":
    defaults = read_ini_data(INI_DEFAULT_FILE)

    if os.path.isfile(CALIBRATION_OVERLAY_FILE):
        overlay = read_ini_data(CALIBRATION_OVERLAY_FILE)
    else:
        overlay = { 'parameters': [],
                    'sections': {} }

    merged = merge_ini_data(defaults, overlay)

    write_ini_data(merged, INI_FILE);
