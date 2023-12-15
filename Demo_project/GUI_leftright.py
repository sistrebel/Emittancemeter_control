# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 14:43:26 2023

@author: silas
"""

import numpy as np
import sys
import os
import time
import os
from PyQt6.QtWidgets import QApplication, QMainWindow,  QMessageBox, \
    QComboBox, QCheckBox, QRadioButton, QGroupBox, QDoubleSpinBox, QSpinBox, QLabel, \
    QPushButton, QProgressBar, QLCDNumber, QSlider, QDial, QInputDialog, QLineEdit, \
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMenu,  \
    QStatusBar, QToolBar, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem, \
    QAbstractItemView, QScrollArea, QStackedWidget, QSizePolicy, QSpacerItem, QLayout, \
    QLayoutItem, QFormLayout, QToolButton,QTextEdit, QTabWidget, QTabBar, QStackedLayout,\
    QVBoxLayout, QWidget,QTextEdit

from PyQt6.QtCore import QCoreApplication, QThread, Qt, pyqtSignal, pyqtSlot, QFile, QTimer,\
    QMetaObject
from PyQt6.QtGui import QIcon, QPixmap,QTextCursor, QTextOption
from PyQt6.uic import loadUi
from PyQt6 import QtCore

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# define all the custom made widgets that are used in the GUI
import threading as Thread
from threading import Thread
import asyncio

#import the other file
#import TMCL_serial_control as control


import pyqtgraph as pg

import random
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets, uic, QtGui


class MainWindow(QMainWindow): 
    
    def __init__(self): #initializing the class
        super().__init__() #super means to load it at the very beginning
       
      
        #connect to the server who does the connection to the device and the communication, start one server (in its own thread ? )
        self.server = control.MotorServer(port='COM7', baud_rate=9600)
        
        
        #these are hardcoded values at the moment!
        #assuming we have 3 motors controlled by one module, all go to the same! at the moment i guess it's because there is only one motor ? 
        self.MODULE_ADRESS_1 = 1 #all have the same module adress 
        self.MODULE_ADRESS_2 = 1
        self.MODULE_ADRESS_3 = 1
        
        self.MOTOR_NUMBER_1 = 0 #would in principle have different motor numbers starting at 0 (first axis)
        self.MOTOR_NUMBER_2 = 0
        self.MOTOR_NUMBER_3 = 0
        
        #initialize three motors with different module adresses
        #those should all be initialized in different threads if possible
        #i initialize the thread by starting the class 
        self.motor1 = control.MotorClient(self.server, self.MODULE_ADRESS_1,self.MOTOR_NUMBER_1) 
        self.motor2 = control.MotorClient(self.server, self.MODULE_ADRESS_2,self.MOTOR_NUMBER_2) #there are no other axis so we do not use those here
        self.motor3 = control.MotorClient(self.server, self.MODULE_ADRESS_3,self.MOTOR_NUMBER_2)
        
        
        """wrong ???"""
        self.motor1.start() #should start the thread ???
        self.motor2.start()
        self.motor3.start()
        
        #initialize the moving axis with the first motor
        self.movingmotor = self.motor1 
        
        #load and connect the GUI
        self.LoadGuis()
        self.connectwidgets()   
        #self.update_plot_data()
        
        
        #initialize the update timer for the position plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(100) #updates every 100ms
        
        #initialize the ready-message for status-message-window
        self.messagetimer = QTimer(self)
        self.messagetimer.timeout.connect(self.ready_message)
        self.messagetimer.start(20000) #updates every 20s
        
        
        self.speed = 7000 #set initial speed if none is selected
        self.Targetposition = 0 #set initial position
        self.sent = False
        
        #do a reference search as soon as it starts 
        self.get_reference() 
        
        #empty lists for saving position plot
        self.all_positions = []
        self.all_times = []
        
     
    """depending on the setting of the Axis-combobox thing the variable self.motor = self.motor1,2 or 3"""
        
    
    def LoadGuis(self):        
        #load main window with uic.loadUI
        #loadUi(r'C:\Users\silas\OneDrive\Documents\PSI Trainee\demo_project\mainwindow\newmainwindow.ui',self) #note that the r"" is important or \\Users....
        loadUi(r"C:\Users\silas\OneDrive\Documents\PSI Trainee\demo_project\mainwindow\Real_mainwindow.ui",self)
        #make a plot 
        
        self.plot() 
        self.createStatusBar()
        
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
        
    def update_plot_data(self):
        """periodically (100ms) updates the position and time of the moving axis (only one axis for now)"""
        
        self.time = self.time[1:] #remove first
        self.time.append(self.time[-1] + 100) #add a new value which is 100ms larger (advanced time)
        
        self.position = self.position[1:]  # Remove the first
        
        newposition = self.motor1.get_position()# Add a new position value
        
        self.position.append(newposition)
    
        self.data_line.setData(np.array(self.time)/1000,self.position) #update the values , divided by 1000 to get seconds
        
        
        leftend = 0
        rightend = 24.5 #measured by moving the sled there!!! #not right probably more like 34....
        
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
            
    # 2. Using .setStatusBar()
    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.statusbar.addPermanentWidget(QLabel(f"Hello")) #example to see if it works...
    
    def ready_message(self):
        self.MessageBox.append(">>"+ "module is ready")
    
    def show_message(self, message):
        """displays the message in the messagebox one can see in the interface"""
        self.MessageBox.append(">>"+ message)
        
    def connectwidgets(self):
        """Connecting the buttons"""
        self.GoleftButton.clicked.connect(self.leftbuttonclick)
        self.GorightButton.clicked.connect(self.rightbuttonclick)
        self.GoleftButton.pressed.connect(self.move_left) #use press and release to have responsive buttons
        self.GorightButton.pressed.connect(self.move_right)
        self.GoleftButton.released.connect(self.stop)
        self.GorightButton.released.connect(self.stop)
        
        self.EndConnectionButton.clicked.connect(self.stop_connection)
        
        self.SavePlotButton.clicked.connect(self.save_plot)
        
        self.SubmitSpeed.clicked.connect(self.retrieve_speed)
        self.SubmitTargetposition.clicked.connect(self.retrieve_position)
        self.SubmitAxis.clicked.connect(self.get_axis)
        #self.AxisBox.clicked.connect(self.get_Axis)
        #self.SubmitTargetposition.clicked.connect(self.goto_position())
        
        
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
            
    def retrieve_directory(self):
        directory = self.textEdit_Directory.toPlainText()
        return directory
    
    def retrieve_speed(self):
        self.speed = self.textEdit_speed.toPlainText()
        self.show_message("new speed:"+ self.speed)
    
    def retrieve_position(self):
        self.Targetposition = self.textEdit_position.toPlainText()
        self.goto_position(self.Targetposition)
        
    def leftbuttonclick(self):
        self.show_message("left button clicked")
        #print("left button clicked")
        time.sleep(0.1) #artificial delay
    
    def rightbuttonclick(self):
         self.show_message("right button clicked")
         #print("right button clicked")
         time.sleep(0.1)
    
    def move_left(self):
        """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
        self.movingmotor.release_break()
        self.movingmotor.start_move_left(self.speed)
        return
    
    def move_right(self):
        """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
        self.movingmotor.release_break()
        self.movingmotor.start_move_right(self.speed)
        return
    def stop(self):
        self.movingmotor.stop_move()
        time.sleep(0.07) #some time to prevent the break to stop the motor to quick
        self.movingmotor.set_break()
        self.show_message("motor stopped")
        return
    def goto_position(self,Target):
        onestep_incm = 0.5/51200 #this is not accurate...
        steps_per_cm = 51200/0.5
        position = float(Target)*steps_per_cm #translate cm position into steps
        self.movingmotor.goto_position(position)
    
    def go_home(self):
        self.movingmotor.release_break()
        self.goto_position(0)
       
       
    def stop_connection(self):
        """this function should stop the movement of all instances and then stops the connection and program"""
        self.go_home()
        self.close() #leaves port closed...
        QApplication.quit()
        return
  
    def get_input(self):
        print("rotate by how many degrees?")
        deg = int(input())
        return deg

    def get_reference(self):
        self.show_message("reference search ongoing")
        self.movingmotor.reference_search()
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


# class TriggerThread(Thread): #is called by move_relative for example to check the movement until the end is reached
#     """
#     Thread that checks every 0.01 seconds if a condition is reached.
#     When the condition is reached, a callback function will be called.
#     """

#     def __init__(self, condition, callback=None, args=(), kwargs={}):
#         """
#         :condition:
#                 Condition that needs to be reached
#         :callback:
#                 Callback function that should be called, when condition is
#                 reached.
#         :args:
#                 is the argument tuple for the target invocation. Defaults to ().
#         :kwargs:
#                 is a dictionary of keyword arguments for the target
#                 invocation. Defaults to {}.
#         """
#         Thread.__init__(self)
#         if kwargs is None:
#             kwargs = {}
#         self._condition = condition
#         self._callback = callback
#         self._args = args
#         self._kwargs = kwargs
#         self.condition_reached = Thread.Event()

#     def run(self):
#         while not self.condition_reached.wait(0.01):
#             if self._condition():
#                 self.condition_reached.set()
#         try:
#             if self._callback:
#                 self._callback(*self._args, **self._kwargs)
#         finally:
#             # Avoid a refcycle if the thread is running a function with
#             # an argument that has a member that points to the thread.
#             del self._callback, self._args, self._kwargs

# class coms():
#     def __init__(self):
#             self.msg = "hello"
#             self.stop = False

#     def printme(self,msg):
#         print(msg)

#     def waitforprint(self):
#         while(not self.stop):
#             if(self.msg != "hello"):
#                 print(self.msg)
#                 self.msg ="hello"






# main window and main launch of the code 

if __name__ == '__main__':
    
    protocol = input("decide which Communication protocol you want to use (e for EPICS, s for Serial):")

    if protocol == "s":
        import New_communications as control
    if protocol == "e":
        import EPICS_specific_communication as control
    
    app = QApplication([])
    window = MainWindow()
    window.show()
    print ("GUI started")
    app.exec()
    
    window.server.stop_server() #stop server and close port after the window has been closed
 
    
    
    # app = QApplication(sys.argv)
    # MainWindow = MainWindow()
    # PlotWindow = ExtraWindow()
    # sys.exit(app.exec_())

    # plotapp = QtWidgets.QApplication(sys.argv)
    # w = ExtraWindow()
    # plotapp.exec_() 
    
