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

import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# define all the custom made widgets that are used in the GUI
import threading as Thread
import asyncio

#import the other file
#import TMCL_serial_control as control

import New_communications as control
#import Communications as control

import pyqtgraph as pg


import sys
import random
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets, uic, QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


import os

class MainWindow(QMainWindow): 
    
    def __init__(self): #initializing the class
        super().__init__() #super means to load it at the very beginning
       
      
        
        self.server = control.MotorServer(port='COM7', baud_rate=9600)
        self.MODULE_ADRESS_1 = 1 #this value should depend on the axis selected in the "Axis combobox
        # Initialize the TMCL motor client for motor 1
        
        self.motor1 = control.MotorClient(self.server, self.MODULE_ADRESS_1)
        
        #initialize the methods
        self.LoadGuis()
        self.connectwidgets()   
        #self.update_plot_data()
        
        
        #update timer for the position plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(100) #updates every 100ms
        
        self.messagetimer = QTimer(self)
        self.messagetimer.timeout.connect(self.ready_message)
        self.messagetimer.start(5000) #updates every 5s
        
        
   
        self.speed = 7000 #set initial speed if none is selected
        self.Targetposition = 0 #set initial position
        self.sent = False
        
        
        self.get_reference() #do a reference search as soon as it starts (maybe make an extra button for it later!!!)
        
        self.all_positions = []
        self.all_times = []
        
        #self.createStatusBar()
        
        
    def LoadGuis(self):        
        #load main window with uic.loadUI
        #loadUi(r'C:\Users\silas\OneDrive\Documents\PSI Trainee\demo_project\mainwindow\newmainwindow.ui',self) #note that the r"" is important or \\Users....
        loadUi(r"C:\Users\silas\OneDrive\Documents\PSI Trainee\demo_project\mainwindow\Real_mainwindow.ui",self)
        
        self.plot() #make a plot with example datasets
        self.createStatusBar()
        
        return
    
    
    def get_axis(self):
        """get the Axis which we want to move in, must have 3 Motorclients now between which i could change then according to the value here"""
        self.Axis = self.AxisBox.currentText() #use this value now to ajdust the rest
        self.show_message("selected " + self.Axis)
        
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
        #self.graphWidget = pg.PlotWidget()
        #self.setCentralWidget(self.graphWidget)
        self.time = [0 for _ in range(100)] #list(range(100))  # 100 time points
        self.position = [0 for _ in range(100)]  # 100 data points
        
        self.data_line =  self.graphWidget.plot(np.array(self.time)/1000, self.position, pen=pen) #divide time by 1000 to get seconds instead of ms
        
        #self.graphWidget.plot(time,position,pen=pen) #create old example plot
        
    
    def update_plot_data(self):
        #print("Hi")
        self.time = self.time[1:] #remove first
        self.time.append(self.time[-1] + 100) #add a new value which is 100ms larger (advanced time)
        
        self.position = self.position[1:]  # Remove the first
        # Add a new position value
        newposition = self.motor1.get_position()
        
        
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
        
        self.statusbar.addPermanentWidget(QLabel(f"Hello"))
    
    def ready_message(self):
        self.MessageBox.append(">>"+ "module is ready")
    
    def show_message(self, message):
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
        self.motor1.release_break()
        self.motor1.start_move_left(self.speed)
        return
    
    def move_right(self):
        self.motor1.release_break()
        self.motor1.start_move_right(self.speed)
        return
    def stop(self):
        self.motor1.stop_move()
        self.show_message("motor stopped")
        return
    
    def goto_position(self,Target):
        onestep_incm = 0.5/51200 #this is not accurate...
        steps_per_cm = 51200/0.5
        position = float(Target)*steps_per_cm #translate cm position into steps
        self.motor1.goto_position(position)
    
    def go_home(self):
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
        self.motor1.reference_search()
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
    app = QApplication([])
    window = MainWindow()
    window.show()
    print ("GUI started")
    app.exec()
    
    
    
    # app = QApplication(sys.argv)
    # MainWindow = MainWindow()
    # PlotWindow = ExtraWindow()
    # sys.exit(app.exec_())

    # plotapp = QtWidgets.QApplication(sys.argv)
    # w = ExtraWindow()
    # plotapp.exec_() 
    
