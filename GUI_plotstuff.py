# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 16:08:29 2023

@author: strebe_s
"""


import numpy as np




#     QComboBox, QCheckBox, QRadioButton, QGroupBox, QDoubleSpinBox, QSpinBox, QLabel, \
#     QPushButton, QProgressBar, QLCDNumber, QSlider, QDial, QInputDialog, QLineEdit, \
#     QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMenu,  \
#     QStatusBar, QToolBar, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem, \
#     QAbstractItemView, QScrollArea, QStackedWidget, QSizePolicy, QSpacerItem, QLayout, \
#     QLayoutItem, QFormLayout, QToolButton,QTextEdit, QTabWidget, QTabBar, QStackedLayout,\
#     QVBoxLayout, QWidget,QTextEdit



import pyqtgraph as pg
import matplotlib
matplotlib.use('Qt5Agg')


from epics import caget


class MainWindow_methods():

    def meas_plot(self):
        """make a plot of the current for each channel
        x channel [1,32] ([1,160] in real verison) and y current
      """
        
        #plotstyle
        self.graphWidget_3.showGrid(x=True, y=True)
        self.graphWidget_3.setTitle("Current-Profile")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget_3.setLabel('left', '2IA [nA]',**styles)
        self.graphWidget_3.setLabel('bottom', 'Channel',**styles)
        pen = pg.mkPen("r") #red line pen
        self.graphWidget_3.setBackground("w") #make white background
        
        #create the plot
        #self.channels = [i for i in range(1, 160 + 1)] #all channels...
        #self.current = [0.00 for _ in range(160)]
        self.channels = [i for i in range(1, 32 + 1)]
        self.current = [0.00 for _ in range(32)]
        
        self.data_line_meas =  self.graphWidget_3.plot(self.channels, self.current, pen=pen) 
        
    def update_plot_meas(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
         """periodically updates the currents of the 32 channels"""
        
         newcurrent_arrayIA = caget('T-MWE2IA:PROF:1') #32 values long
         # newcurrent_arrayIB = caget('T-MWE2IA:PROF:1')
         # newcurrent_arrayIC = caget('T-MWE2IA:PROF:1')
         # newcurrent_arrayID = caget('T-MWE2IA:PROF:1')
         # newcurrent_arrayIE = caget('T-MWE2IA:PROF:1')
         #newcurrent_array = newcurrent_arrayIA +newcurrent_arrayIB+newcurrent_arrayIC+newcurrent_arrayID + newcurrent_arrayIE #all 160 channels
         
         newcurrent_array = newcurrent_arrayIA
         
         self.current = np.array(newcurrent_array)
         self.data_line_meas.setData(self.channels,self.current) 
    
    
    def xy_plot(self):
        """make a 2D plot of the collimator position - x horizontal and y vertival.
        Should be displayed when a scan is started and forms a snake after a scan."""
        
        #plotstyle
        self.graphWidget_2.showGrid(x=True, y=True)
        self.graphWidget_2.setTitle("xy-plot")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget_2.setLabel('left', 'Position 1Y [mm]', **styles)
        self.graphWidget_2.setLabel('bottom', 'Position 1X [mm]', **styles)
        pen = pg.mkPen("r") #red line pen
        self.graphWidget_2.setBackground("w") #make white background
        
        #create the plot
        self.horizontal = [] 
        self.vertical = []  
        
        self.data_line_xy =  self.graphWidget_2.plot(self.horizontal, self.vertical, pen=pen) 
        
    
    def update_plot_xy(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
        """periodically (100ms) updates the position and time  """
        
        newhorizontal =  self.steps_to_mm(self.motor1.get_position(),"1X")
        newvertical = self.steps_to_mm(self.motor2.get_position(),"1Y")
        
        self.horizontal.append(newhorizontal) 
        self.vertical.append(newvertical)
        
        self.data_line_xy.setData(self.horizontal,self.vertical) 
    
            
    def plot(self): #this is the important bit where you can modify the plot window
        """make a 2D plot of position vs time embedded into the QWidget Window (named 'graphWidget') provided in the loaded mainwindow"""
        #plotstyle
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setTitle("Position-plot")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget.setLabel('left', 'Position [mm]', **styles)
        self.graphWidget.setLabel('bottom', 'Time [s]', **styles)
        #self.graphWidget.LegendItem()
        self.graphWidget.addLegend()
        pen1 = pg.mkPen("r") #red line pen
        pen2 = pg.mkPen("g")
        pen3 = pg.mkPen("b")
        self.graphWidget.setBackground("w") #make white background
        
        #create the plot
        self.time = [0 for _ in range(100)] #list(range(100))  # 100 time points
        self.position_1 = [0 for _ in range(100)]  # 100 data points
        self.position_2 = [0 for _ in range(100)]
        self.position_3 = [0 for _ in range(100)]
        
        
        
        self.data_line1 =  self.graphWidget.plot(np.array(self.time), self.position_1, pen=pen1, name="1X") #divide time by 1000 to get seconds instead of ms
        self.data_line2 =  self.graphWidget.plot(np.array(self.time), self.position_2, pen=pen2,name="1Y") #divide time by 1000 to get seconds instead of ms
        self.data_line3 =  self.graphWidget.plot(np.array(self.time), self.position_3, pen=pen3, name="2Y") #divide time by 1000 to get seconds instead of ms
        
    def update_plot_data(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
        """periodically (100ms) updates the position and time of the moving axis (only one axis for now)"""
        
        self.time = self.time[1:] #remove first
        self.time.append(self.time[-1] + 100) #add a new value which is 100ms larger (advanced time)
        
        self.position_1 = self.position_1[1:]  # Remove the first
        self.position_2 = self.position_2[1:]  # Remove the first
        self.position_3 = self.position_3[1:]  # Remove the first
        
        
        newposition_1 = self.steps_to_mm(self.motor1.get_position(),"1X") #in mm #self.server.issue_motor_command(self.movingmotor, ("get_position",),1)#self.motor1_queue.put(("get_position",))
        newposition_2 = self.steps_to_mm(self.motor2.get_position(),"1Y")
        newposition_3 = self.steps_to_mm(self.motor3.get_position(),"2Y")
        
        self.position_1.append(newposition_1)
        self.position_2.append(newposition_2)
        self.position_3.append(newposition_3)
    
        self.data_line1.setData(np.array(self.time)/1000,self.position_1) #update the values , divided by 1000 to get seconds
        self.data_line2.setData(np.array(self.time)/1000,self.position_2)
        self.data_line3.setData(np.array(self.time)/1000,self.position_3)
        
        """use this to determine when to change the endstop displays"""
        status = self.movingmotor.Get(self.movingmotor.pv_motor_status)
        if status == 0x9: #display the endstop status
            self.left_endstop_display()
            if self.sent == False:
                self.show_message("upper end reached!")
                self.sent = True
        elif status == 0xA:
            self.right_endstop_display() 
            if self.sent == False:
                self.show_message("lower end reached!")
                self.sent = True
        else:   #reset the endstop status
            self.reset_endstop_display()
            self.sent = False
            
        while len(self.all_times) < 100000: #safe space... 
            self.all_positions1.append(newposition_1)
            self.all_positions2.append(newposition_2)
            self.all_positions3.append(newposition_3)
            self.all_times.append(self.time[-1])