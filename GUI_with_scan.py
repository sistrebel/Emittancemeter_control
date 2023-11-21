# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:35:58 2023

@author: strebe_s
"""





"""scan processing application"""

"""two motors one for x and one for y, add a 'scan' button with which i can start a scan"""


import numpy as np
import sys
import os
import time


import queue

from PyQt5.QtWidgets import QApplication, QMainWindow,  QMessageBox, \
    QComboBox, QCheckBox, QRadioButton, QGroupBox, QDoubleSpinBox, QSpinBox, QLabel, \
    QPushButton, QProgressBar, QLCDNumber, QSlider, QDial, QInputDialog, QLineEdit, \
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMenu,  \
    QStatusBar, QToolBar, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem, \
    QAbstractItemView, QScrollArea, QStackedWidget, QSizePolicy, QSpacerItem, QLayout, \
    QLayoutItem, QFormLayout, QToolButton,QTextEdit, QTabWidget, QTabBar, QStackedLayout,\
    QVBoxLayout, QWidget,QTextEdit

from PyQt5.QtCore import QCoreApplication, QThread, Qt, pyqtSignal, pyqtSlot, QFile, QTimer
    

from PyQt5.uic import loadUi
from PyQt5 import QtCore

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import threading as Thread
import asyncio

import EPICS_specific_communication as control

import pyqtgraph as pg

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets, uic, QtGui

from threading import Lock

import scan_script

class MainWindow(QMainWindow): 
    
    def __init__(self): #initializing the class
        super().__init__() #super means to load it at the very beginning
       
       
        #connect to the server who does the connection to the device and the communication
        self.server = control.MotorServer() #only one server 
        
  
        #would in principle have different motor numbers starting at 0 (first axis)
        self.MOTOR_NUMBER_1 = 1 #horizontal collimator
        self.MOTOR_NUMBER_2 = 2 #vertical collimator
        self.MOTOR_NUMBER_3 = 3 #vertical readout
        
        #total grid dimensions in steps
        self.x_length = 50000
        self.y_length = 4000
        
        #initialize the motor queues
        self.motor1_queue =  queue.Queue()
        self.motor2_queue =  queue.Queue()
        self.motor3_queue =  queue.Queue()
        
        #create the motor instances
        self.motor1 = self.server.create_and_start_motor_client(self.server, self.MOTOR_NUMBER_1, self.motor1_queue)
        self.motor2 = self.server.create_and_start_motor_client(self.server, self.MOTOR_NUMBER_2, self.motor2_queue)
        self.motor3 = self.server.create_and_start_motor_client(self.server,  self.MOTOR_NUMBER_3, self.motor3_queue)
        
    
        #initialize the moving axis with the first motor
        self.movingmotor = self.motor1
        
        #load and connect the GUI
        self.LoadGuis()
        self.connectwidgets()   
        
        #make a plot 
        self.plot() 
        self.createStatusBar()
        
        
        #initialize the update timer for the position plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(100) #updates every 100ms
        
        #initialize the update timer for the xy-plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot_xy)
        self.timer.start(100) #updates every 100ms
        
        #initialize the ready-message for status-message-window
        self.messagetimer = QTimer(self)
        self.messagetimer.timeout.connect(self.ready_message)
        self.messagetimer.start(20000) #updates every 20s
        
        
        self.speed = 500 #set initial speed if none is selected
        self.Targetposition = 0 #set initial position
        self.sent = False
        
        
        #do a reference search as soon as the applications starts
        #self.get_reference() 
        
        #empty lists for saving position plot
        self.all_positions = []
        self.all_times = []
        
        
    
    def LoadGuis(self):        
        #load main window with uic.loadUI
        #note that the r"" is important or \\Users....
        loadUi(r"Real_mainwindow.ui",self) #adjust this one to specific place
        return
    
    def get_axis(self):
        """get the Axis which the user wants to move in;
        assuming 3 Motorclients between which the user selects in the comboBox"""
        Axis = self.AxisBox.currentText() #use this value now to ajdust the rest
        self.show_message("selected " + Axis)
        
        if Axis == "Axis 1":
            self.movingmotor = self.motor1
        if Axis == "Axis 2":
            self.movingmotor = self.motor2
        if Axis == "Axis 3":
            self.movingmotor = self.motor3
        
    
    def xy_plot(self):
        """make a 2D plot of the collimator position
        x horizontal and y vertival
        
        Should be displayed when a scan is started and forms a snake after a scan. """
        
        #plotstyle
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setTitle("xy-plot")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget.setLabel('left', 'Position [cm]', **styles)
        self.graphWidget.setLabel('bottom', 'Time [s]', **styles)
        pen = pg.mkPen("r") #red line pen
        self.graphWidget.setBackground("w") #make white background
        
        #create the plot
        self.horizontal = [] #list(range(100))  # 100 time points
        self.vertical = []  # 100 data points
        
        self.data_line =  self.graphWidget.plot(self.horizontal, self.vertical, pen=pen) #divide time by 1000 to get secon
        
    
    def update_plot_xy(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
        """periodically (100ms) updates the position and time of the moving axis (only one axis for now)"""
        
        
        #newhorizontal = ... """get current horizontal position"""
        #newvertical = ... """get current verzital position"""
        #self.horizontal.append(newhorizontal) 
        #self.vertical.append(newvertical)
        
        

        #self.data_line.setData(self.horizontal,self.vertical) #update the values , divided by 1000 to get seconds
        
        
    def plot(self): #this is the important bit where you can modify the plot window
        """make a 2D plot of position vs time embedded into the QWidget Window (named 'graphWidget') provided in the loaded mainwindow"""
        #plotstyle
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setTitle("Position-plot")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget.setLabel('left', 'Position [cm]', **styles)
        self.graphWidget.setLabel('bottom', 'Time [s]', **styles)
        pen = pg.mkPen("r") #red line pen
        self.graphWidget.setBackground("w") #make white background
        
        #create the plot
        self.time = [0 for _ in range(100)] #list(range(100))  # 100 time points
        self.position = [0 for _ in range(100)]  # 100 data points
        
        self.data_line =  self.graphWidget.plot(np.array(self.time), self.position, pen=pen) #divide time by 1000 to get seconds instead of ms
        
    def update_plot_data(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
        """periodically (100ms) updates the position and time of the moving axis (only one axis for now)"""
        
        self.time = self.time[1:] #remove first
        self.time.append(self.time[-1] + 100) #add a new value which is 100ms larger (advanced time)
        
        self.position = self.position[1:]  # Remove the first
        
        newposition = self.server.issue_motor_command(self.movingmotor, ("get_position",),1)#self.motor1_queue.put(("get_position",))
        
        
        self.position.append(newposition)
    
        self.data_line.setData(np.array(self.time)/1000,self.position) #update the values , divided by 1000 to get seconds
        
        
        """use this data to determine when to change the displays"""
        
        leftend = 0
        rightend = 30 #measured by moving the sled there!!! #not right probably more like 34 (?)....
        
        if newposition <= leftend+0.1: #display the endstop status
            self.left_endstop_display()
            if self.sent == False:
                self.show_message("left end reached! reverse now")
                self.sent = True
        elif newposition >= rightend-0.1:
            self.right_endstop_display() 
            if self.sent == False:
                self.show_message("right end reached! reverse now")
                self.sent = True
        else:   #reset the endstop status
            self.reset_endstop_display()
            self.sent = False
            
        #save all data in a list for when plot is created later.
        self.all_positions.append(newposition)
        self.all_times.append(self.time[-1])
        
    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.statusbar.addPermanentWidget(QLabel(f"Hello i am the Demo Project")) #example to see if it works...
    
    def ready_message(self):
        self.MessageBox.append(">>"+ "module is ready")
    
    def show_message(self, message):
        """displays the message in the messagebox one can see in the interface"""
        self.MessageBox.append(">>"+ message)
        
    def connectwidgets(self):
        """Connecting the buttons"""
        self.GoleftButton.clicked.connect(self.leftbuttonclick)
        self.GorightButton.clicked.connect(self.rightbuttonclick)
        self.GoleftButton.pressed.connect(self.move_backwards) #use press and release to have responsive buttons
        self.GorightButton.pressed.connect(self.move_forwards)
        self.GoleftButton.released.connect(self.stop)
        self.GorightButton.released.connect(self.stop)
        
        self.EndConnectionButton.clicked.connect(self.stop_connection)
        
        self.SavePlotButton.clicked.connect(self.save_plot)
        
        self.SubmitSpeed.clicked.connect(self.retrieve_speed)
        self.SubmitTargetposition.clicked.connect(self.retrieve_position)
        self.SubmitAxis.clicked.connect(self.get_axis)
    
        """add scan button and connect it to the 'scan' function which i want to run in a separate script for readability"""
        self.ScanButton.clicked.connect(self.retrieve_numberofpoints) #gets data and starts scan script
        # self.PauseScanButton.clicked.connect(scan_script.pause_scan)
        # self.ContinueScanButton.clicked.connect(scan_script.continue_scan)
        
        
    def save_plot(self):
        """saves the position vs time plot to the dedicated directory"""
        
        directory = self.retrieve_directory
    
        fig = plt.figure()
        plt.xlabel("Time [s]")
        plt.ylabel("Position [cm]")
        plt.grid()
        plt.plot(self.all_times, self.all_positions)
        
        if directory != None:
            fig.savefig(directory + '/graph.png')
            self.show_message("Plot saved to "+ directory+ "as 'graph.png' ")
            
    """might put the retrieve data methods into its own file/class"""
            
    def retrieve_numberofpoints(self):
        """get number of points for scan"""
        points = int(self.textEdit_Points.toPlainText()) #maybe this is wrong
        if points > 0:
            scan_script.start_scan(self.motor1,self.motor2,self.motor3,points,self.x_length,self.y_length,self.server) #starts the scan with #points measurementpoints in the grid 
        else:
            self.show_message("INVALID VALUE")
    def retrieve_directory(self):
        directory = self.textEdit_Directory.toPlainText()
        return directory
    
    def retrieve_speed(self):
        """get the speed from the MainWindow and set the global variable speed to its value"""
        self.speed = self.textEdit_speed.toPlainText()
        self.server.issue_motor_command(self.movingmotor_queue,("set_speed",self.speed))
        self.show_message("new speed:"+ self.speed)
    
    def retrieve_position(self):
        """get position from MainWindow and start the go to position function"""
        self.Targetposition = int(self.textEdit_position.toPlainText())
        self.goto_position(self.Targetposition)
        
    def leftbuttonclick(self):
        self.show_message("left button clicked")
        #print("left button clicked")
        time.sleep(0.05) #artificial delay
    
    def rightbuttonclick(self):
         self.show_message("right button clicked")
         #print("right button clicked")
         time.sleep(0.05)
    
    """change the way i send commands, use the issue commands function instead of doing it directly!!!"""
    
    def move_backwards(self): #backwards
        """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
        self.server.issue_motor_command(self.movingmotor_queue, ("release_brake",))
        self.server.issue_motor_command(self.movingmotor_queue, ("move_backwards",self.speed))
        
    
    def move_forwards(self): #forwards
        """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
        self.server.issue_motor_command(self.movingmotor_queue, ("release_brake",))
        self.server.issue_motor_command(self.movingmotor_queue, ("move_forwards",self.speed))
        
    def stop(self):
        self.server.issue_motor_command(self.movingmotor_queue, ("stop_move",))
        self.show_message("motor stopped")
        return
   
    def goto_position(self,Target):
        """motor moves to specified Target-position given in cm"""
        # onestep_incm = 1.1/100000 # 0.5/51200 #this is not accurate...
        # steps_per_cm = 100000/1.1 #51200/0.5
        # position = float(Target)*steps_per_cm #translate cm position into steps
        
        
        self.server.issue_motor_command(self.movingmotor_queue,("release_brake",))
        time.sleep(0.1)
        self.server.issue_motor_command(self.movingmotor_queue, ("go_to_position",Target))
        
        # while not self.server.issue_motor_command(self.movingmotor_queue, ("position_reached",),1):
        #     time.sleep(0.1)
        self.server.issue_motor_command(self.movingmotor_queue, ("set_brake",))
        #self.show_message("position reached")
    
    def go_home(self,stop = False):
        """moves motor to initial position and if stop == True the server connection is stopped and port closed"""
       
        
        self.server.issue_motor_command(self.movingmotor_queue, ("release_brake",))
        
        time.sleep(0.1)
        self.server.issue_motor_command(self.movingmotor_queue, ("go_to_position",0))
        # while not self.server.issue_motor_command(self.movingmotor_queue, ("position_reached",),1):
        #     time.sleep(0.1)
        self.server.issue_motor_command(self.movingmotor_queue, ("set_brake",))
        
        time.sleep(0.2) #wait until the command was processed
        
        if stop == True:
            self.server.stop_server()
       
    def stop_connection(self):
        """this function should stop the movement of all instances and then stops the connection and program"""
        self.go_home(stop = True) #go home and stop the conection 
        self.server.stop_server()
        QApplication.quit()
        return
  
    def get_reference(self):
        self.show_message("reference search ongoing")
        #self.movingmotor_queue.put(("reference_search",))
        self.server.issue_motor_command(self.movingmotor_queue, ("reference_search",))
        #self.movingmotor.reference_search()
        self.show_message("reference search done")
        
    def right_endstop_display(self):
        self.RightstopDisplay.display(1)
        return
    def left_endstop_display(self):
        self.LeftstopDisplay.display(1)
        return
    def reset_endstop_display(self):
        self.LeftstopDisplay.display(0)
        self.RightstopDisplay.display(0)
        
        
        
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    print ("GUI started")
    app.exec()