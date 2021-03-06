# FBGUI-README: FBG Baking and Calibration UI

## Overview

 * The project contains a configurable baking, and calibration program
   both accessible through a tkinter GUI.
 * Both programs are contained in the same Application, and each application
   contains widgets to configure settings, a realtime graphing display of
   the results, and an excel format generator for the results.

## Getting Started
 * The project requires Python 3 and NIVisa
   - The required python modules are listed in the requirements.txt file
   - These can be run, assuming python and pip are in the machines path
     by running the command:
     ```pip install -r requirements.txt```
 * Detailed source code documentation is available in the docs folder
 * A detailed document describing how to setup the computers is
     included in the docs folder, called ProgramSetup.html.
 * Source code documentation is available at https://ehmurray8.github.io/KytonUI

## Detailed Usage

### Running the Code
 * The program can be run from source once all the requirements have been
   installed running ```python ./main_program.py``` from within the fbgui
   directory will launch the gui.
 * An executable can also be created using PyInstaller, and this can be
   used to run the program without python installed.
   - NiVisa still needs to be installed in order to run the program,
     more details can be found in the ProgramSetup.html file.

#### Building the installer, and executable
 * Python3 version <= 3.5 is required with PyInstaller installed to build
   the installer and program executable, both of these are setup to
   run only on windows machines
 * There is a batch file in the main directory, called build.bat, used for creating the
   executable files, make sure the file is pointing to the correct location
   of where Python (<= 3.5) is installed on your machine, for the two PyInstaller
   commands.
 * Run the following command from a windows terminal in the main source code project directory:
 ```commandline
 ./build.bat
 ```
 * Once both scripts are done executing a folder called dist\install_fbgui,
   will be created, and in the folder the file install_fbgui.exe can be
   used to install the program on a computer
 * Running install_fbgui.exe will install the code in the
   $USER\AppData\Local\Program\FbgUI folder, will create a desktop shortcut,
   and a start menu entry for the program
   - The installer will also create a desktop entry for the documentation, as well
     as a Start Menu entry for the documentation.

### Using the Program
 * There are 3 main tabs on the program ui: the home screen, the baking
   program, and the calibration program
   - Each program tab has 3 tabs: the configuration screen, the graphing
     screen, and the data screen

### Main Screen
 * The main screen contains entries to configure the locations of the
   devices required for running the program:
   - The Micron Optics SM125 and Optical Switch are looking for IP
     addresses, and ports respectively
   - The LSC Temp Controller, and Delta Oven are looking for valid
     GPIB addresses (i.e. GPIB0::12::INSTR)
 * This screen also contains a program log used for displaying log messages,
   a dropdown box to filter messages by severity, and a button to
   export the log messages to a txt file in the fbgui\log folder
 * The screen also contains a list of the program runs used for creating
   excel files, selecting a program name and then clicking the generate
   spreadsheet button will create a spreadsheet and open it in Excel, the
   refresh button can be used to load new runs of the program.

### Bake Program
 * The bake program is used for recording points continuously at a set temperature
   for an infinite amount of time, until the program is paused.

#### Options Screen
 * This screen sets up a baking program run, and has the following options:
   - **Number of laser scans** - this configures the number of laser scans to take
     for each reading and use to average for that reading
   - **Baking Temperature** - temperature in C to set the oven to for the bake,
     if this field is empty, the oven will not be used for the bake.
   - **Primary time interval** - the time in hours to wait between taking
     data points
   - **Drift Rate** - once this drift rate is reached the program will begin
     recording points
   - **Excel File Name** - the name of the excel file to store the eventual
     output spreadsheet, the file name must end in .xlsx, and must be uniquely
     named, changing the file path does not classify as being unique
   - **FBG inputs** - FBGs can be added each channel, and can be named using
     the entry input, and a switch position can be specified for the FBG by
     using the spinbox

### Calibration Program
 * The calibration program is used for recording wavelength and power readings
   for a set of specified temperatures.

#### Options Screen
 * This screen sets up a calibration program run and has the following options:
   - **Use Cooling** - If checked use the oven cooling function
   - **Number of laser scans** - this configures the number of laser scans to take
     for each reading and use to average for that reading
   - **Number of temperature readings** - the number of temperature readings
     to average together to use for calculating the drift rate
   - **Time between temp readings** - The frequency at which to check the drift
     rate
   - **Number of Cal Cycles** - The number of calibration cycles to run
   - **Target Temps** - Comma separated list of the temperatures to use for
     the calibration run
   - **Excel file name** - Same as Baking (See Above)
   - **FBG inputs** - Same as Baking (See Above)

### General Program Screens
 * The graphing, and data tabs are roughly the same for both the calibration and
   baking programs

#### Graphing Screen
 * The graphing screen contains a grid of 6 graphs displaying the data that is
   being recorded
 * Double clicking on one of the graphs will display a zoomed view of the graph
 * The toolbar in the lower left corner can be used for interacting with the graph
   - The pause button will stop the graph animation to allow the user to interact
     with the graphs and zoom in, the animation will not continue until the play
     button is pressed

#### Data Screen
 * The data screen shows a table view of the last 100 recorded points, and
   can be used to look at new data that is being recorded
   - Each column of the table can be sorted by clicking on the header
 * The Create Excel button at the bottom of the screen will create an excel
   spreadsheet of the current running program

## Program Notes
 * If the program was running, not paused, when the program was closed or
   the power shut off the program will start up using the last used configuration.
   If you would like to change the configuration you must press the pause button
   first.
 * The log view on the homescreen should display relevant information about
   the current status of the program and should be the first place that is checked
   if something appears to be wrong.
 * If there is an issue try closing the program, and reopening it.
 * Pressing F11 will toggle full screen mode.
 * The program stores data in a sqlite database called program_data.db
   located in the db folder.
   - Creating a copy of this datbase would be a good way to backup data
     and move data between computers.
   - If the program appears to be slowing down or not working after a while it is
     possible the database may be too full, and moving the database to a different location
     would allow the program to start with a fresh database. The old database
     can be switched in for the new database at any time to look at old data.
   - If attempting to change databases always make sure to keep a backup copy of
     the database, and to put the database in the db folder and name it
     program_data.db.

### Additional Details

 * The source code documentation was generated using the sphinx tool.
 * The source code documentation options are configured in the sphinx-source directory.
   - The conf.py file in this directory contains configuration information for how the
     source code documentation will be generated.
   - The index.rst file is used for pointing sphinx in the right direction to find
     all of the source code. A fbgui.rst file can be created by running the command:
     ```sphinx-apidoc.exe -o .\sphinx_source .\fbgui```
     from the main directory, and then rename fbgui.rst to index.rst, for sphinx to use it.
   - The make.bat file is used to create the docs, and this is called within the build.bat
     script.
   - You may need to change the directories in the sphinx_source\conf.py file
     to point to the code on your machine.
 * The executable configuration options are in the file fbgui.spec, and the installer
   configuration options are in the install.spec file.
 * Known issue: The zoomed wavelength vs. power graph xlabel doesn't appear,
   the bottom righthand corner of the screen displays the x and y coordinates
   of the cursor.

### Program Setup Notes

#### GPIB

 * Make sure the NIVisa program is installed on the target machine, this program
   enables the usage of USB GPIB hubs, and allows python to talk with the NIVisa
   program.
   - Install location: www.ni.com/download/ni-488.2/7272/en
   - The program will warn you if NIVisa is not installed when it starts
 * Right computer defaults:
     * **Lake Shore Cryotronics 340 Default GPIB Address:** GPIB0::12::INSTR
     * **Delta Oven Default GPIB Address:** GPIB0::27::INSTR
 * Left computer defaults:
     * **Lake Shore Cryotronics 332 Default GPIB Address:** GPIB0::13::INSTR
     * **Delta Oven Default GPIB Address:** GPIB10::27::INSTR

#### Ethernet

 * Make sure the computer and all of the devices are on the same subnet.
 * **Optical Switch:** defaults to 192.168.1.111, to change the IP address and port,
   press enter, and then the down arrow 2 times, and then enter gets you to
   the IP address. Moving the arrows up and down will change the address,
   and enter will confirm the highlighted selection.
 * **Micron Optics** to change the Micron Optics IP Address, you must use the
   Micron Optics Enlight program and the network configuration can be found in
   the settings tab.
Notes can abo