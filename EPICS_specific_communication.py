# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 16:10:59 2023

@author: silas
"""

"""EPICS dedicated script, """



import epics
from epics import PV, camonitor
import threading
from queue import Queue

from threading import Thread
#do not work with pyTMCL but try to use the classes directly and adjust them if needed! --> do not send via two different connections anymore...

#import pyTMCL

# from bus import Bus
# from motor import Motor
# from commands import Command
# from reply import Reply
# from init import connect

import time
import re

#import pyTMCL

#import motor

from AllpyTMCL_classes import*

#import random #for testing

import GUI_leftright as gui

# Server class to send motor control commands to a queue and receive messages


class MotorServer: #not even necessary i think...
    def __init__(self, port, baud_rate):
        
        threading.Thread.__init__(self)
        """get a connection to epics here"""
         #from init, this returns all methods form the Bus class, so we do not need any other method which "sends" directly to the serial port
        self.epics_port = ...
        
        # self.command_queue = Queue()
        
        # #self.send_thread = threading.Thread(target=self.send_command)
        
        # self.receive_thread = threading.Thread(target=self.receive_messages) #this will run in a separate thread to continuously "listen" to the serial port
        # self.receive_thread.daemon = True
        # self.receive_thread.start()
        # self.running = True #to stop the server
        
        # self.reading = threading.Condition()
        # self.isreading = False

        
    def send_command(self, command, value): #sends the commands into a queue, or command item if such a structure is provided i guess
        """this sends the command to the  blocks the port until an answer is received, look at Bus.py"""
        #self.bus.send(address = 1, command, type =, motorbank = , value) 
       
            #print(response)
    #def send_command_with_response(self,)
    
    def doRead(self,ser,term):
        print("isreading")
        tout = 0.01
        matcher = re.compile(term)    #gives you the ability to search for anything
        tic     = time.time()
        buff    = ser.read(128)
        # you can use if not ('\n' in buff) too if you don't like re
        while ((time.time() - tic) < tout) and (not matcher.search(buff)):
           buff += ser.read(128)

        return buff

    def receive_messages(self): #does work but not with my commands from TMCL sadly, super unstable somehow...., can't read anything coming from TMCL
        """function which i can't use while still doing things directly with TMCL port. In principle though 
        this should work and i can use the isreading parameter to control it"""
        
        
        while True: #check continuously for a response
            #print(self.serial_port.in_waiting) #always 0 i.e. no response in waiting queue
            #time.sleep(0.2)
                if self.epics_port.in_waiting:
                    self.epics_port.isreading = True
                    #time.sleep(0.1)
                    print("message came back!!!") #readline() or readlines()!!!!
                    received_message = self.doRead(self.epics_port, term='\n') #self.serial_port.readline().decode('utf-8').strip() #this is a problem, can't decode message which is returned
                    #self.serial_port.readline().decode('utf-8').strip()
                    #time.sleep(0.01) #make sure there is enough time
                    #print("Received message:", received_message) 
                    #print("out")
                    received_message = "mymessage"
                    self.isreading = False
                    gui.window.show_message(received_message) #would send the received message to the messagebox
                    return
        return
    
    def stop_server(self): #make sure that when running it again the serial port is accessible
        self.running = False
        self.epics_port.close()
        
    def start(self): #sends everything that is put into the queue
        try:
            while self.running:
                print("is reading:", self.isreading)
                if not self.command_queue.empty():# and self.isreading:
                    print("is reading:", self.isreading)
                    command = self.command_queue.get() #command_item = self.command_queue.get()#
                    
                    # command = command_item['command'] #extra bit
                    # response_queue = command_item['response_queue']
                    
                    self.send_command(command)
                    
                    # #extra bit for reading response
                    # if self.serial_port.in_waiting:
                    #     response = self.serial_port.readline().decode('utf-8').strip()
                        
                    #     print("response", response)
                        
                    self.command_queue.task_done()
        
        except KeyboardInterrupt:
            self.epics_port.close()
            print("Exiting...")

# Client class to control a TMCL stepper motor
class MotorClient(Thread): #i don't know if Thread is necessary
    
    def __init__(self, server, MODULE_ADDRESS):  
    
        threading.Thread.__init__(self) #i should initiate each MotorClient in its own thread!!!, don't know if this is right...
        #print("started a new thread")
        self.server = server
        print(MODULE_ADDRESS)
        #self.MODULE_ADDRESS = MODULE_ADDRESS #creates a motor instance for each axis
        
        self.motorconn = ... #whatever method it will take
        
        #self.axisparameter = AxisParameterInterface(self.motorconn)  #changed from motor... #returns connection to the Axisparameter class 
        
        self.position = 0
        
        
        #initialize the pv's i am using here 
        self.pv_break = PV('XXX:m1.VAL') #change the names of record usw accordingly... prolly specific to the motor which is initialized ?
        self.pv_speed = PV('XXX:m1.VAL')
        self.pv_position = PV('XXX:m1.VAL')
        self.pv_targetposition = PV('XXX:m1.VAL')
        self.pv_targetreached = PV('XXX:m1.VAL')
        self.pv_leftstopstatus = PV('XXX:m1.VAL')
        self.pv_rightstopstatus = PV('XXX:m1.VAL')
        self.pv_reference = PV('XXX:m1.VAL')
    
        
    
        def Set(self,pv,value):
            """resets the value of a passed process variable"""
            pv.put(value)
    #     command
    #     self.server.command_queue.put(command)
    
        def Get(self,pv):
            return pv.get(value)
    #     self.motorconn.get_axis_parameter(param)
        
    # def invalid_command(self):
    #     self.motorconn.send(234,0,2,1) 
        
        
        def release_break(self):
           # self.motorconn.send(14,0,2,1)# f"{self.motor_id} move {steps}\n"
            #self.server.command_queue.put(command)
            set(self.pv_break,1) #0 or 1        
        def set_break(self):
            #self.motorconn.send(14,0,2,0)
            #pv_break.put(0) #the opposite of the above!
                Set(self.pv_break,0)
            
        def start_move_left(self, speed): #the designated commands in this case for TMCL but could be adjusted 
                Set(self.pv_speed,speed) #assuming left is positive orientation
        
        def start_move_right(self, speed): #the designated commands in this case for TMCL but could be adjusted 
                self.Set(self.pv_speed,-speed)
            
            
      
        def stop_move(self):
                Set(self.pv_speed,0)
                self.set_break()
        
            
            #self.motorconn.stop()
            #self.server.command_queue.put(command)


        def goto_position(self,position):
                travellingspeed = 100 #whatever number is adequate
                if position > self.get_position():
                        self.Set(self.pv_speed,-travellingspeed)
                        while(self.pv_targetreached==False):
                            time.sleep(0.05) #wait until position is reached
                        self.Set(self.pv_speed, 0) #stop when target is reached
                        self.set_break()
                    
            
        def get_position(self):
                position = self.get(self.pv_position)
                return position
            
            #51200 steps ~ 0.5 cm #not accurate...
                onestep_incm = 0.5/51200
                numberofsteps = self.axisparameter.actual_position
                position = numberofsteps * onestep_incm
            
                leftend = 0
                rightend = 38.9 #measured by moving the sled there!!!
                if position <= leftend: #make sure the sled does not move beyond endstops!!!
                    self.start_move_right(5000)
                    time.sleep(1)
                    self.stop_move()
                #gui.right_endstop_display() #it's a problem...
                #gui.MainWindow.show_message("left end reached! reverse now")
                #print("left end reached! reverse now")
                #return "left_end"
                if position >= rightend:
                    self.start_move_left(5000)
                    time.sleep(1)
                    self.stop_move()
                #gui.MainWindow.show_message("right end reached! reverse now")
                #gui.window.left_endstop_display() #call a function that will display a sign like on whiteboard
                #print("right end reached! reverse now")
                #return "right_end"
            #else: gui.reset_endstop_display()
            
        return position #self.axisparameter.actual_position #random.randint(0,100)
            
        def get_speed(self):
                speed = self.motorconn.get_axis_parameter(3)
            #self.server.command_queue.put(command)
            #print("sent")
                return speed
        
        def rightstop_status(self):
                return self.axisparameter.rightstop_readout()
            
        def leftstop_status(self):
                return self.axisparameter.leftstop_readout()
        
        def pps_to_rpm(self,v_pps): #standard values for a TMCL-1260
                """translate pulsepersecond to rev per minute"""
                v_rps = v_pps/(200*256)
                return 60*v_rps
            
        def position_reached():
                return self.motorconn.get_position_reached()
            
        def reference_search(self): #should of course be handled with interrupts but does not work for some reason...who can i ask...
                """move motor to the very left until endstop is triggered. 
                Immediately stop and identify this position as '0'"""
                self.release_break()
                self.start_move_left(15000)
            #self.server.command_queue.put(command) #those did not do anything anymore... the commands are being sent in the very first line anyway
            #self.server.command_queue.put(command1)
            
                endstop = 0
                print("starting reference search")
                while endstop == 0:
                    endstop = self.rightstop_status() #self.axisparameter.rightstop_readout()#self.server.command_queue.get()
                
                    time.sleep(0.2) #short interval but not to long in order not to damage the thing
            #print("loop ended")
                self.stop_move()
            #self.server.command_queue.put(command2)
                time.sleep(0.2) #make sure it actually stopped
                self.axisparameter.set(1,0)
            #self.server.command_queue.put(command3)
                position = self.axisparameter.actual_position
                print("endstop position initialized as '0'")
                print("position:", position)
                return
  