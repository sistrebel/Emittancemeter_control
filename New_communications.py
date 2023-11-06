# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 09:33:36 2023

@author: silas
"""


"""this script should act as a server which handles the communication. It should have a queue where the tasks from the QT GUI are sent to and then they should go to the device."""
"""every single command should give a response"""

import serial
import threading
from queue import Queue

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


class MotorServer:
    def __init__(self, port, baud_rate):
        
        #threading.Thread.__init__(self)
        self.thread = threading.Thread(target=self.run(port, baud_rate))
        
        
    def run(self,port,baud_rate):
            self.serial_port = serial.Serial(port, baud_rate)
            self.bus = connect(self.serial_port) #from init, this returns all methods form the Bus class, so we do not need any other method which "sends" directly to the serial port
            time.sleep(3)
        
    def is_thread_running(self):
        return self.thread.is_alive()
    
    def start_thread(self):
        self.thread.start()
        # self.command_queue = Queue()
        
        # #self.send_thread = threading.Thread(target=self.send_command)
        
        # self.receive_thread = threading.Thread(target=self.receive_messages) #this will run in a separate thread to continuously "listen" to the serial port
        # self.receive_thread.daemon = True
        # self.receive_thread.start()
        # self.running = True #to stop the server
        
        # self.reading = threading.Condition()
        # self.isreading = False
    # def close_port(self):
    #     self.bus.close()
    
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
                if self.serial_port.in_waiting:
                    self.isreading = True
                    #time.sleep(0.1)
                    print("message came back!!!") #readline() or readlines()!!!!
                    received_message = self.doRead(self.serial_port, term='\n') #self.serial_port.readline().decode('utf-8').strip() #this is a problem, can't decode message which is returned
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
        self.serial_port.close()
        print("port closed")
        
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
            self.serial_port.close()
            print("Exiting...")

# Client class to control a TMCL stepper motor
class MotorClient(Thread): #i don't know if Thread is necessary
    
    def __init__(self, server, MODULE_ADDRESS, MOTOR_NUMBER):  
    
        threading.Thread.__init__(self) #i should initiate each MotorClient in its own thread!!!, don't know if this is right...
        #print("started a new thread")
        self.server = server
        print(MODULE_ADDRESS)
        #self.MODULE_ADDRESS = MODULE_ADDRESS #creates a motor instance for each axis
         
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
        self.motorconn = server.bus.get_motor(MODULE_ADDRESS,MOTOR_NUMBER) #MODULE_ADDRESS #returns the connection to the motor with Axis-number (MODULE_ADDRESS).
        
        self.axisparameter = AxisParameterInterface(self.motorconn)  #changed from motor... #returns connection to the Axisparameter class 
        
        self.position = 0
        
        
        
    """TODO: rewrite this as with get and set method s.t. i have properties like breaks on, position, moving, speed"""
    """ the thing is that it does not make a hole lot of sense if i am still using another class where the get/set has already been done."""
    """ i could however write MY OWN communication protocol that does not use the service of pyTMCL for example"""
    
    # def set(self,param,value):
    #     command
    #     self.server.command_queue.put(command)
    
    # def get(self,param):
    #     self.motorconn.get_axis_parameter(param)
        
    def invalid_command(self):
        self.motorconn.send(234,0,2,1)

    
    def release_break(self):
        self.motorconn.send(14,0,2,1)# f"{self.motor_id} move {steps}\n"
        #self.server.command_queue.put(command)
    
    def set_break(self):
        self.motorconn.send(14,0,2,0)
        
    def start_move_left(self, speed): #the designated commands in this case for TMCL but could be adjusted 
        self.motorconn.rotate_left(speed)# f"{self.motor_id} move {steps}\n"
        #command2 = self.motorconn.stop()
        #self.server.command_queue.put(command1)
        #time.sleep(0.5)
        #self.server.command_queue.put(command2)
    
    def start_move_right(self, speed): #the designated commands in this case for TMCL but could be adjusted 
        self.motorconn.rotate_right(speed)# f"{self.motor_id} move {steps}\n"
        #command2 = self.motorconn.stop()
        #command1 = self.motorconn.move_relative(51200) #360 degrees in steps
        #self.server.command_queue.put(command1) 
        #time.sleep(0.5) #for continuous movement
        #self.server.command_queue.put(command2)
  
    def stop_move(self):
        self.motorconn.stop()
        #self.server.command_queue.put(command)


    def goto_position(self,position):
        self.motorconn.move_absolute(position)
        #self.server.command_queue.put(command)
        
    def get_position(self):
        """TODO!!: return the position value. Define the LEFT endstop as "position 0" 
        then count the revolutions for figuring out the actual position."""
        #print("HEY")
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
#motorconn = bus.get_motor(MODULE_ADDRESS)
    # Add other motor control functions here

    # def close_connection(self):
    #     self.server.close_port()

# Usage
if __name__ == "__main__": #is only excecuted if the program is started by itself and not if called by others
    # Initialize the server
    server = MotorServer(port='COM7', baud_rate=9600) 
    print("Thread is running:", server.is_thread_running())
    server.start_thread()
    print("Thread is running:", server.is_thread_running())
    
    MODULE_ADRESS = 1
    MOTOR_NUMBER = 0
    # Initialize the TMCL motor client for motor 1
    motor1 = MotorClient(server, MODULE_ADRESS, MOTOR_NUMBER)
     
    motor1.start()
    """if there were several motors you could then use more MotorClients instead of just one"""



  


    
    
    try:
        # Example: Move motor 1 by 1000 steps
        motor1.release_break()
        motor1.start_move_right(7000)
        endstop_status = motor1.rightstop_status()
        print(endstop_status)
        #motor1.server.close_port()
        time.sleep(5)
        
        # endstop = 0
        #motor1.invalid_command()
        # print("hi")
        # #motor1.get_speed() #this one should trigger 
        # speed = motor1.motorconn.get_axis_parameter(3) #this gives me the value directly but that means i do not go through the server
        # endstop = motor1.axisparameter.rightstop_readout() #this works!!!
        # print(endstop)
        # #res = motor1.server.receive_thread
        # #print(res)
        
        # motor1.start_move_left(7000)
        # #time.sleep(10)
        motor1.stop_move() #does not clash
        
        #motor1.close_connection()
        
        #motor1.start_move_right(4444 )
        
        server.stop_server() #stop server after series of commands, listening thread keeps running otherwise
        
    except KeyboardInterrupt:
        server.stop_server()
        print("the server has stopped")
    # Add more motor control commands and client instances as needed  import time



# class TestCondition(object): #change this for my endstop condition
#     def __init__(self):
#             #self.bool = False
#             self.endstop = False
            
#     def get_condition(self):
#             return self.endstop

#     def callback(arg1, arg2): 
#         print(arg1)
#         print(arg2)
#         print("endstop reached!!!")
#         motor1.stop_move()

#     def test(callback=None, args=(), kwargs=None):
#         condition = TestCondition()
#         args = args
#         kwargs = kwargs
#         if callback is not None:
#             TriggerThread(condition=condition.get_condition,
#                           callback=callback, args=args, kwargs=kwargs).start()
#             #time.sleep(3)
#             #condition.endstop = True
#             condition.endstop = motor1.rightstop_status()
#             print(condition.endstop)
#     test(callback=callback, args=("test1", "test2"))