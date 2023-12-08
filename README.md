# Emittancemeter_control
***
## Table of Contents
1. [General Info](#general-info)
2. [GUI](#gui)
3. [Communnication](#communication)
4. [Scan](#scan)
5. [Calculation](#calculation)

## General Info
***
This project provides a rudimentary control software for the 4D Emittancemeter.

The software is split into the following python scripts:
      *GUI*,
      *Communication script*,
      *Scan script & measurement class*,
      *Calculation script*.

You can run the application by cloning the repository and running the GUI in python3. 
The other scripts will run in the background.
Make sure epice you have access to the PyQt5, epics and threading libraries.


## GUI
***
The GUI consists of one class called MainWindow in which the .ui file is loaded and all the widgets are connected to functions. The Window is divided into a scan section (right) and a manual control section (left).
In the scan section one has to input the desired scan specifications like the speed and the grid dimensions. The with proper inputs the scan be started. An approximate Start- and End-time is displayed.
In the manual control section one can select the axis and move the motor on the selected axis to a target position with a desired speed. Before using it one should calibrate the system.



## Communication
***

## Scan
***

## Calculation
***


