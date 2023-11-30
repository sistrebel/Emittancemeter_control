# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:35:58 2023

@author: strebe_s
"""





"""scan processing application"""

"""two motors one for x and one for y, add a 'scan' button with which i can start a scan"""


import numpy as np
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

from PyQt5.QtCore import QTimer
    

from PyQt5.uic import loadUi


import matplotlib.pyplot as plt



import EPICS_specific_communication as control

import pyqtgraph as pg

import matplotlib
matplotlib.use('Qt5Agg')


import threading

import scan_script

from epics import caget

class MainWindow(QMainWindow): 
    
    def __init__(self): #initializing the class
        super().__init__() #super means to load it at the very beginning
       
       
        #connect to the server who does the connection to the device and the communication
        self.server = control.MotorServer() #only one server 
        
  
        #would in principle have different motor numbers starting at 0 (first axis)
        self.MOTOR_NUMBER_1 = 1 #horizontal collimator
        self.MOTOR_NUMBER_2 = 2 #vertical collimator
        self.MOTOR_NUMBER_3 = 3 #vertical readout
        
        # #total grid dimensions in steps
        # self.x_length = 50000
        # self.y_length = 4000
        
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
        self.Axis = "1X"
        

        #load and connect the GUI
        self.LoadGuis()
        self.connectwidgets()   
        
        #make a plot 
        self.plot() 
        self.xy_plot()
        self.meas_plot()
        self.createStatusBar()
        
        """comment this out because i keep getting the User Timeout warning from reading the waveform too often..."""
        #initialize the update timer for meas plot
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot_meas)
        self.timer.start(1000) #updates every 1000ms
        
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
        
        
        self.speed = self.movingmotor.Get(self.movingmotor.pv_speed_get)#set initial speed if none is selected
        self.Targetposition = 0 #set initial position
        self.sent = False
        self.allcalibrated = False
        
        self.start_message_thread()
        
        #do a reference search as soon as the applications starts
        #self.get_reference() 
        
        #empty lists for saving position plot
        self.all_positions1 = []
        self.all_positions2 = []
        self.all_positions3 = []
        self.all_times = []
        
        self.end_scan = 0
        
        
    def cleanup_on_exit(self):
        # Trigger cleanup actions here
        print("Cleaning up before exit")
        self.show_message(">> recalibrate and close")
        self.calibration()
        if self.motor1.iscalibrating == False and self.motor1.iscalibrating == False and self.motor3.iscalibrating == False:
            self.motor1.stop_motor()
            self.motor2.stop_motor()
            self.motor3.stop_motor()
            self.server.stop_server()
      
        
    def stop_connection(self):
        """Closes the application and the window, by doing this the Qt AboutToQuit method triggers "cleanup_on_exit" 
        so it doesn't matter if the application is closed via "x" or "close" the same thing happens"""
        QApplication.quit() 
        QApplication.closeAllWindows()

    def LoadGuis(self):        
        loadUi(r"Real_mainwindow.ui",self) #adjust this one to specific place, now it must be saved at in the same folder as the GUI script
        
    
    def connectwidgets(self):
        """Connecting the buttons"""
        # self.GoleftButton.clicked.connect(self.leftbuttonclick)
        # self.GorightButton.clicked.connect(self.rightbuttonclick)
        # self.GoleftButton.pressed.connect(self.move_backwards) #use press and release to have responsive buttons
        # self.GorightButton.pressed.connect(self.move_forwards)
        # self.GoleftButton.released.connect(self.stop)
        # self.GorightButton.released.connect(self.stop)
        
        self.StopButton.clicked.connect(self.stopmotor)
        self.RunButton.clicked.connect(self.runmotor)
        
        self.EndConnectionButton.clicked.connect(self.stop_connection)
        
        self.SavePlotButton.clicked.connect(self.save_plot)
        
        self.SubmitSpeed.clicked.connect(self.retrieve_speed)
        self.SubmitTargetposition.clicked.connect(self.retrieve_position)
        self.SubmitAxis.clicked.connect(self.get_axis)
    
        """add scan button and connect it to the 'scan' function which i want to run in a separate script for readability"""
        self.ScanButton.clicked.connect(self.start_scan_thread) #gets data and starts scan script
        self.PauseScanButton.clicked.connect(scan_script.pause_scan)
        self.ContinueScanButton.clicked.connect(scan_script.continue_scan)
        self.StopScanButton.clicked.connect(scan_script.stop_scan)
        
        self.CalibrateButton.clicked.connect(self.calibration)
        

    
    def meas_plot(self):
        """make a plot of the current for each channel
        x channel [1,32] and y current
        
      """
        
        #plotstyle
        self.graphWidget_3.showGrid(x=True, y=True)
        self.graphWidget_3.setTitle("Current-Profile")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget_3.setLabel('left', 'Current 2IA [nA]', **styles)
        self.graphWidget_3.setLabel('bottom', 'Channel', **styles)
        pen = pg.mkPen("r") #red line pen
        self.graphWidget_3.setBackground("w") #make white background
        
        #create the plot
        self.channels = [i for i in range(1, 32 + 1)]
        self.current = [0.00 for _ in range(32)]
        
        self.data_line_meas =  self.graphWidget_3.plot(self.channels, self.current, pen=pen) 
        
    def update_plot_meas(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
         """periodically updates the currents of the 32 channels"""
        
         newcurrent_array = caget('T-MWE2IA:PROF:1') #pv_IA_wave.get() #32 values long
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
        self.horizontal = [] #list(range(100))  # 100 time points
        self.vertical = []  # 100 data points
        
        self.data_line_xy =  self.graphWidget_2.plot(self.horizontal, self.vertical, pen=pen) 
        
    
    def update_plot_xy(self): #only one plot, data is received for the currently moving one...maybe when you change them there is a problem then
        """periodically (100ms) updates the position and time  """
        
        newhorizontal =  self.steps_to_mm(self.motor1.get_position(),"1X")
        newvertical = self.steps_to_mm(self.motor2.get_position(),"1Y")
        self.horizontal.append(newhorizontal) 
        self.vertical.append(newvertical)
        
        if self.motor1.iscalibrating == False and self.motor2.iscalibrating == False and  self.motor3.iscalibrating == False:
            self.data_line_xy.setData(self.horizontal,self.vertical) 
        else:
            self.horizontal = []
            self.vertical = []
            
    def plot(self): #this is the important bit where you can modify the plot window
        """make a 2D plot of position vs time embedded into the QWidget Window (named 'graphWidget') provided in the loaded mainwindow"""
        #plotstyle
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setTitle("Position-plot")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphWidget.setLabel('left', 'Position [mm]', **styles)
        self.graphWidget.setLabel('bottom', 'Time [s]', **styles)
        pen1 = pg.mkPen("r") #red line pen
        pen2 = pg.mkPen("g")
        pen3 = pg.mkPen("b")
        self.graphWidget.setBackground("w") #make white background
        
        #create the plot
        self.time = [0 for _ in range(100)] #list(range(100))  # 100 time points
        self.position_1 = [0 for _ in range(100)]  # 100 data points
        self.position_2 = [0 for _ in range(100)]
        self.position_3 = [0 for _ in range(100)]
        
        self.data_line1 =  self.graphWidget.plot(np.array(self.time), self.position_1, pen=pen1) #divide time by 1000 to get seconds instead of ms
        self.data_line2 =  self.graphWidget.plot(np.array(self.time), self.position_2, pen=pen2) #divide time by 1000 to get seconds instead of ms
        self.data_line3 =  self.graphWidget.plot(np.array(self.time), self.position_3, pen=pen3) #divide time by 1000 to get seconds instead of ms
        
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
        
        """use this data to determine when to change the displays"""
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
            
        #save all data in a list for when plot is created later.
        
        while len(self.all_times) < 100000: #safe space... 
            self.all_positions1.append(newposition_1)
            self.all_positions2.append(newposition_2)
            self.all_positions3.append(newposition_3)
            self.all_times.append(self.time[-1])
        
    def createStatusBar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.statusbar.addPermanentWidget(QLabel(f"Emittance Scan GUI")) #example to see if it works...
    
    def ready_message(self):
        if self.allcalibrated:
            self.MessageBox.append(">>"+ "module is ready")
        else:
            self.MessageBox.append(">>"+ "calibrate first")
    
    def start_show_time_thread(self):
        """starts a thread that checks the content of the message_queue"""
        self.show_scan_time_queue = queue.Queue()
        self.thread = threading.Thread(target=self.run_show_time_thread)
        self.thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        self.thread.start()
        
    
    def run_show_time_thread(self):  
        """constantly checks the message_queue and passes the messages to the messagebox"""
        self.done_showing = False
        while True and self.server.running and self.done_showing == False:
                # if not self.server.running:
                #     break
                try:
                        message = self.show_scan_time_queue.get_nowait() #waits for 1s unit to get an answer #get_nowait() #command should be of the format command = [command_name, *args]
    
                        self.show_scan_time(str(message[0]),str(message[1]))
                        self.done_showing = True #only do it once and then stop this thread
                except:
                        if self.show_scan_time_queue.empty():
                            pass
                        else: 
                            print("something worse happened")
                            
    def start_message_thread(self):
        """starts a thread that checks the content of the message_queue"""
        self.message_queue = queue.Queue()
        self.thread = threading.Thread(target=self.run_message_thread)
        self.thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        self.thread.start()
    
    def run_message_thread(self):  
        """constantly checks the message_queue and passes the messages to the messagebox"""
        while True and self.server.running:
                # if not self.server.running:
                #     break
                try:
                        message = self.message_queue.get_nowait() #waits for 1s unit to get an answer #get_nowait() #command should be of the format command = [command_name, *args]
                        self.show_message(message)
                except:
                        if self.message_queue.empty():
                            pass
                        else: 
                            print("something worse happened")
    
    
    def show_message(self, message):
        """displays the message in the messagebox one can see in the interface"""
        self.MessageBox.append(">>"+ message)
        
    
    def save_plot(self):
        """saves the position vs time plot to the dedicated directory"""
        
        directory = self.retrieve_directory
    
        fig = plt.figure()
        plt.xlabel("Time [s]")
        plt.ylabel("Position [cm]")
        plt.grid()
        plt.plot(self.all_times, self.all_positions1)
        plt.plot(self.all_times, self.all_positions2)
        plt.plot(self.all_times, self.all_positions3)
        try:
            fig.savefig(directory + '/graph.png')
            self.show_message(">> Plot saved to "+ directory+ "as 'graph.png' ")
        except:
            self.show_message("No valid directory ")
    
        
    def get_axis(self):
        """get the Axis which the user wants to move in;
        assuming 3 Motorclients between which the user selects in the comboBox"""
        self.Axis = self.AxisBox.currentText() #use this value now to ajdust the rest
        self.show_message("selected " + self.Axis)
        
        if self.Axis == "1X":
            self.movingmotor = self.motor1
        if self.Axis == "1Y":
            self.movingmotor = self.motor2
        if self.Axis == "2Y":
            self.movingmotor = self.motor3
    
    
    def show_scan_time(self,start_time,end_time):
        """displays the start and end time of the scan which was just started"""
        # self.MessageBox_StartTime.clear()
        # self.MessageBox_EndTime.clear()
        
        self.MessageBox_StartTime.append(str(start_time))
        self.MessageBox_EndTime.append(str(end_time))    
    
    def get_setup_val(self):
        """retrieves all the setup values for the next scan form the GUI"""
        x_min = self.mm_to_steps(float(self.textEdit_MWE1X_MIN.toPlainText()),"1X")
        x_max = self.mm_to_steps(float(self.textEdit_MWE1X_MAX.toPlainText()),"1X")
        x_speed = self.mm_to_steps(float(self.textEdit_MWE1X_SPEED.toPlainText()),"1X")
        
        x_setup_val = (x_min,x_max,x_speed)
        
        y_min = self.mm_to_steps(float(self.textEdit_MWE1Y_MIN.toPlainText()),"1Y")
        y_max = self.mm_to_steps(float(self.textEdit_MWE1Y_MAX.toPlainText()),"1Y")
        y_speed = self.mm_to_steps(float(self.textEdit_MWE1Y_SPEED.toPlainText()),"1Y")
        
        y_setup_val = (y_min,y_max,y_speed)
        
        y2_min = self.mm_to_steps(float(self.textEdit_MWE2Y_MIN.toPlainText()),"2Y")
        y2_max = self.mm_to_steps(float(self.textEdit_MWE2Y_MAX.toPlainText()),"2Y")
        y2_speed = self.mm_to_steps(float(self.textEdit_MWE2Y_SPEED.toPlainText()),"2Y")
    
        
        y2_setup_val = [y2_min,y2_max,y2_speed]
        
        #get the voltages... would be set by this 
        MWE1U = float(self.textEdit_MWE1U.toPlainText()) #set with ISEG power supply
        MWE2U = float(self.textEdit_MWE2U.toPlainText()) #set to SEU-blende
        
        return x_setup_val, y_setup_val, y2_setup_val, MWE1U, MWE2U
    
    def start_scan_thread(self):
        """Starts the scan procedure with the parameters specified in the GUI, the scan script will run on a separate thread"""
        
        resolution_x = float(self.textEdit_Resolution_x.toPlainText()) #retrieve resolution in mm
        resolution_y = float(self.textEdit_Resolution_y.toPlainText())
        resolution_z = float(self.textEdit_Resolution_z.toPlainText())
        
        # x_length = 21700
        # y_length = 104000
        # z_length = 9000
        
        x1_setup_val, y1_setup_val, y2_setup_val, MWE1U, MWE2U = self.get_setup_val()
        
        meshsize_x = self.mm_to_steps(resolution_x,"1X")
        meshsize_y = self.mm_to_steps(resolution_y,"1Y")
        meshsize_z = self.mm_to_steps(resolution_z,"2Y")
        
        
        
        if self.checkBox_2.isChecked():
            goinsteps = True
        else:
            goinsteps = False
        
        if self.checkBox.isChecked():
            saveit = True
        else:
            saveit = False
        
        
        meas_freq = float(self.textEdit_MeasFreq.toPlainText()) #get measurement frequency
        
        y2_speed = self.steps_to_mm(y2_setup_val[2],"2Y")
        
        fidelity = meas_freq/y2_speed #how many meas points per mm
        
        if goinsteps == False:
            self.textBrowser_Fidelity.clear()
            self.textBrowser_Fidelity.append(str(fidelity))#maybe change this... to another format instead of using append()
        else: self.textBrowser_Fidelity.clear()
        
        if resolution_x > 0 and resolution_y > 0 and resolution_z > 0:
            #self.start_show_time_thread()
            
            scan_thread = threading.Thread(target=scan_script.start_scan, args=(saveit,meas_freq,goinsteps,self.message_queue,self.show_scan_time,self.motor1,self.motor2,self.motor3,meshsize_x,meshsize_y,meshsize_z,x1_setup_val,y1_setup_val,y2_setup_val, self.server))
            scan_thread.daemon = True
            scan_thread.start()
        
            
        else:
            self.show_message("INVALID VALUE")
    
    def retrieve_directory(self):
        directory = self.textEdit_Directory.toPlainText()
        return directory
    
    def retrieve_speed(self):
        """get the speed from the MainWindow and set the global variable speed to its value"""
        speed = float(self.textEdit_speed.toPlainText()) #in mm/s
        self.speed = self.mm_to_steps(speed,self.Axis) #in steps/s
        
        self.server.issue_motor_command(self.movingmotor,("set_speed",self.speed))
        self.show_message("new speed: " + str(self.speed) + " [steps/s] " + str(speed) + " [mm/s]")
    
    def retrieve_position(self):
        """get position from MainWindow and start the go to position function"""
        self.Targetposition = int(self.textEdit_position.toPlainText()) #input in mm
        axis = self.Axis
        self.Targetposition = self.mm_to_steps(self.Targetposition,axis) #convert to steps
        self.goto_position(self.Targetposition)

    def leftbuttonclick(self):
        self.show_message("left button clicked")
        #print("left button clicked")
        time.sleep(0.05) #artificial delay
    
    def rightbuttonclick(self):
         self.show_message("right button clicked")
         #print("right button clicked")
         time.sleep(0.05)
    
    def steps_to_mm(self,steps,axis): 
        """ converts steps to mm for the particular axis i.e. string "1X","1Y" and "2Y" """
        
        if axis == "1X": #1X
            mm = steps/535
        elif axis == "1Y": #1Y
            mm = steps/800
        elif axis == "2Y": #2Y
            mm = steps/50
        else: print("ERROR, NO VALID AXIS")
        
        return mm
            
    def mm_to_steps(self,mm,axis):
        """ converts mm to steps for the particular axis i.e. string "1X","1Y" and "2Y" """
        
        if axis == "1X":
            steps = mm*535
        elif axis == "1Y":
            steps = mm*800
        elif axis == "2Y":
            steps = mm*50
        else: print("ERROR, NO VALID AXIS")
        
        return steps
    
    def calibration(self):
        """starts calibration for all three motors"""
        self.server.issue_motor_command(self.motor1,("calibrate",))
        self.server.issue_motor_command(self.motor2,("calibrate",))
        self.server.issue_motor_command(self.motor3,("calibrate",))
        # self.motor2.calibration()
        # self.motor3.calibration()
        
        self.allcalibrated = True
    
    # def move_backwards(self): #backwards
    #     """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
    #     self.server.issue_motor_command(self.movingmotor, ("release_brake",))
    #     self.server.issue_motor_command(self.movingmotor, ("move_backwards",self.speed))
        
    
    # def move_forwards(self): #forwards
    #     """starts the movement of "motor" (i.e. self.motor1,2 or 3) """
    #     self.server.issue_motor_command(self.movingmotor, ("release_brake",))
    #     self.server.issue_motor_command(self.movingmotor, ("move_forwards",self.speed))
        
    # def stop(self):
    #     self.server.issue_motor_command(self.movingmotor, ("stop_move",))
    #     self.show_message("motor stopped")
    #     return
    
    def stopmotor(self):
        self.movingmotor.Set(self.movingmotor.pv_stopstatus,1)
        self.movingmotor.ismoving = False
    def runmotor(self):
        self.movingmotor.Set(self.movingmotor.pv_stopstatus,0)
   
    def goto_position(self,Target):
        """motor moves to specified Target-position given in mm by passing the command"""
        self.server.issue_motor_command(self.movingmotor, ("go_to_position",Target))
        
       
    def right_endstop_display(self):
        self.RightstopDisplay.display(1)
   
    def left_endstop_display(self):
        self.LeftstopDisplay.display(1)
       
    def reset_endstop_display(self):
        self.LeftstopDisplay.display(0)
        self.RightstopDisplay.display(0)
        
        
        
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    print ("GUI started")
    app.aboutToQuit.connect(window.cleanup_on_exit)
    app.exec()