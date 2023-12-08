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

You can run the application by cloning the repository and running the GUI with python3 in a Terminal that has access to all the * EPICS process variables*
The other scripts will run in the background. They run on *separate threads*.

Make sure you have access to the *PyQt5*, *epics* and *threading* libraries.


## GUI
***
The GUI consists of one class called MainWindow in which the .ui file is loaded and all the widgets are connected to functions. The Window is divided into a scan section (right) and a manual control section (left).

In the scan section one has to input the desired scan specifications like the speed and the grid dimensions. The with proper inputs the scan be started. An approximate Start- and End-time is displayed.

In the manual control section one can select the axis and move the motor on the selected axis to a target position with a desired speed. Before using it one should calibrate the system.

## Communication
***
The communication with the hardware is done through the *EPICS* control system. The behaviour is controlled by chaning the state of various *process variables*.

Every motor is an instance of the class *MotorClient* and runs on a separate thread, they all have the same functionalities. These instances are created and controlled via the *MotorServer* class. The GUI and Scan script issue commands through this.

The *process variables* are accessibel through *epics.PV* and their states can be changed with *epics.PV.put()/get()*.

## Scan
***
A scan is started from the GUI. It opens up a new thread where the program goes through the hole scan procedure. **A scan might take a long time!**
The measured data (in the form of a numpy array) will be saved to a data.npy file. 

## Calculation
***
Loads the data.npy file from memory. The array is converted into a convenient shape and the divergence angle is calculated at each measurement location.
An automatic ellipse fit is made and the area is estimated. **!!!this is not finished/not tested with any real dataset!!!**

