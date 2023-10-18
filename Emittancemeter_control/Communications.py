#-*- coding: utf-8 -*-
"""
Created on Thu Oct  5 17:16:19 2023

@author: silas
"""

"""this script should act as a server which handles the communication. It should have a queue where the tasks from the QT GUI are sent to and then they should go to the device."""
"""every single command should give a response"""

import serial
import threading
from queue import Queue
import pyTMCL
import time
import re



import motor

import random #for testing


import GUI_leftright as gui

# Server class to send motor control commands to a queue and receive messages

class MotorServer:
    def __init__(self, port, baud_rate):
        
        self.serial_port = serial.Serial(port, baud_rate)
        self.bus = pyTMCL.connect(self.serial_port) #adjusted for pyTMCL bus instance
        self.command_queue = Queue()
        
        #self.send_thread = threading.Thread(target=self.send_command)
        
        self.receive_thread = threading.Thread(target=self.receive_messages) #this will run in a separate thread to continuously "listen" to the serial port
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.running = True #to stop the server
        
        self.reading = threading.Condition()
        self.isreading = False
        
        
    # def create_bus(self):
    #     bus = pyTMCL.connect(self.serial_port)
    #     return bus
        
    def send_command(self, command): #sends the commands into a queue, or command item if such a structure is provided i guess
        
        while not self.isreading: #the problem again is that i do not send everything through my designated server so i can't really stop the "sending" of messages when doing it directly...
            print("is sending")
            self.serial_port.write(command.encode())
            
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
                    #received_message = self.doRead(self.serial_port, term='\n') #self.serial_port.readline().decode('utf-8').strip() #this is a problem, can't decode message which is returned
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
class MotorClient:
    
    def __init__(self, server, MODULE_ADDRESS):
        self.server = server
        self.MODULE_ADDRESS = MODULE_ADDRESS #creates a motor instance for each axis
        self.motorconn = server.bus.get_motor(MODULE_ADDRESS)
        
        self.axisparameter = motor.AxisParameterInterface(self.motorconn)
        
        self.position = 0
        
        
    """TODO: rewrite this as with get and set method s.t. i have properties like breaks on, position, moving, speed"""
    """ the thing is that it does not make a hole lot of sense if i am still using another class where the get/set has already been done."""
    """ i could however write MY OWN communication protocol that does not use the service of pyTMCL for example"""
    
    # def set(self,param,value):
    #     command
    #     self.server.command_queue.put(command)
    
    # def get(self,param):
    #     self.motorconn.get_axis_parameter(param)
        
    
    
    def release_break(self):
        command = self.motorconn.send(14,0,2,1)# f"{self.motor_id} move {steps}\n"
        self.server.command_queue.put(command)
    
    def start_move_left(self, speed): #the designated commands in this case for TMCL but could be adjusted 
        command1 = self.motorconn.rotate_left(speed)# f"{self.motor_id} move {steps}\n"
        #command2 = self.motorconn.stop()
        self.server.command_queue.put(command1)
        #time.sleep(0.5)
        #self.server.command_queue.put(command2)
    
    def start_move_right(self, speed): #the designated commands in this case for TMCL but could be adjusted 
        command1 = self.motorconn.rotate_right(speed)# f"{self.motor_id} move {steps}\n"
        #command2 = self.motorconn.stop()
        #command1 = self.motorconn.move_relative(51200) #360 degrees in steps
        self.server.command_queue.put(command1) 
        #time.sleep(0.5) #for continuous movement
        #self.server.command_queue.put(command2)
  
    def stop_move(self):
        command = self.motorconn.stop()
        self.server.command_queue.put(command)


    def goto_position(self,position):
        command = self.motorconn.move_absolute(position)
        self.server.command_queue.put(command)
        
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
        command = self.motorconn.get_axis_parameter(3)
        self.server.command_queue.put(command)
        #print("sent")
        return
        
    def pps_to_rpm(self,v_pps): #standard values for a TMCL-1260
        """translate pulsepersecond to rev per minute"""
        v_rps = v_pps/(200*256)
        return 60*v_rps
        
    def reference_search(self): #should of course be handled with interrupts but does not work for some reason...who can i ask...
        """move motor to the very left until endstop is triggered. 
        Immediately stop and identify this position as '0'"""
        command = self.release_break()
        command1 = self.start_move_left(15000)
        self.server.command_queue.put(command)
        self.server.command_queue.put(command1)
        
        endstop = 0
        print("loop starts")
        while endstop == 0:
            #print("still looking")
            #time.sleep(5)
            endstop = self.axisparameter.rightstop_readout()#self.server.command_queue.get()
            #self.server.command_queue.put(endstop)
            #for the sake of time and clarity i will now send my command directly in this function
            #it does not go via server but as the actual server will be via EPICS anyway i should probably get going
            #endstop = self.server.receive_messages()
            #print(endstop)
            time.sleep(0.2) #short interval but not to long in order not to damage the thing
        #print("loop ended")
        command2 = self.stop_move()
        self.server.command_queue.put(command2)
        time.sleep(0.2) #make sure it actually stopped
        command3 = self.axisparameter.set(1,0)
        self.server.command_queue.put(command3)
        position = self.axisparameter.actual_position
        print("endstop position initialized as '0'")
        print("position:", position)
        return
#motorconn = bus.get_motor(MODULE_ADDRESS)
    # Add other motor control functions here

# Usage
if __name__ == "__main__":
    # Initialize the server
    server = MotorServer(port='COM7', baud_rate=9600)
    MODULE_ADRESS_1 = 1
    # Initialize the TMCL motor client for motor 1
    motor1 = MotorClient(server, MODULE_ADRESS_1)

    try:
        # Example: Move motor 1 by 1000 steps
        # motor1.release_break()
        # motor1.start_move_right(7000)
        # time.sleep(2)
        # endstop = 0
        # print("hi")
        # #motor1.get_speed() #this one should trigger 
        # speed = motor1.motorconn.get_axis_parameter(3) #this gives me the value directly but that means i do not go through the server
        # endstop = motor1.axisparameter.rightstop_readout() #this works!!!
        # print(endstop)
        # #res = motor1.server.receive_thread
        # #print(res)
        
        # motor1.start_move_left(7000)
        # #time.sleep(10)
        # motor1.stop_move() #does not clash
        
        server.stop_server() #stop server after series of commands, listening thread keeps running otherwise
        
    except KeyboardInterrupt:
        
        server.stop_server()
        print("the server has stopped")
    # Add more motor control commands and client instances as needed
