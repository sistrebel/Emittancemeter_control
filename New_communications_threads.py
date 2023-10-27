# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:45:18 2023

@author: silas
"""

import serial
import threading
import queue 

import time

from AllpyTMCL_classes import*


#Define a global lock for the serial port such that only one thread at a time can use it
serial_port_lock = threading.Lock() 

class MotorServer:
    def __init__(self, port, baud_rate):
       
     
        self.serial_port = serial.Serial(port, baud_rate)
        self.bus = connect(self.serial_port) #from AllpyTMCL_classes; init, this returns all methods form the Bus class, so we do not need any other method which "sends" directly to the serial port
       
    def send_command(self, command, value): 
        """this sends the command to the  blocks the port until an answer is received, look at Bus.py, not necessary for working with TMCL"""
        #self.bus.send(address = 1, command, type =, motorbank = , value)
       
    #def send_command_with_response(self,)
   
    # def doRead(self,ser,term):
    #     print("isreading")
    #     tout = 0.01
    #     matcher = re.compile(term)    #gives you the ability to search for anything
    #     tic     = time.time()
    #     buff    = ser.read(128)
    #     # you can use if not ('\n' in buff) too if you don't like re
    #     while ((time.time() - tic) < tout) and (not matcher.search(buff)):
    #        buff += ser.read(128)

    #     return buff

    # def receive_messages(self): #does work but not with my commands from TMCL sadly, super unstable somehow...., can't read anything coming from TMCL
    #     """function which i can't use while still doing things directly with TMCL port. In principle though
    #     this should work and i can use the isreading parameter to control it"""
       
       
    #     while True: #check continuously for a response
    #         #print(self.serial_port.in_waiting) #always 0 i.e. no response in waiting queue
    #         #time.sleep(0.2)
    #             if self.serial_port.in_waiting:
    #                 self.isreading = True
    #                 #time.sleep(0.1)
    #                 print("message came back!!!") #readline() or readlines()!!!!
    #                 received_message = self.doRead(self.serial_port, term='\n') #self.serial_port.readline().decode('utf-8').strip() #this is a problem, can't decode message which is returned
    #                 #self.serial_port.readline().decode('utf-8').strip()
    #                 #time.sleep(0.01) #make sure there is enough time
    #                 #print("Received message:", received_message)
    #                 #print("out")
    #                 received_message = "mymessage"
    #                 self.isreading = False
    #                 gui.window.show_message(received_message) #would send the received message to the messagebox
    #                 return
    #     return
   
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
                   
                    # #extra bit for reading response, 
                    # if self.serial_port.in_waiting: 
                    #     response = self.serial_port.readline().decode('utf-8').strip()
                       
                    #     print("response", response)
                       
                    # self.command_queue.task_done()
                    
        except KeyboardInterrupt:
            self.serial_port.close()
            print("Exiting...")
    
    def create_and_start_motor_client(self,server, MODULE_ADRESS, MOTOR_NUMBER, command_queue):
        motor = MotorClient(server, MODULE_ADRESS, MOTOR_NUMBER, command_queue)
        motor.start_motor()
        thread = threading.Thread(target=motor.run)
        thread.start()

    def issue_motor_command(self,command_queue,command_data, isreturn = 0):
        result_queue = queue.Queue()
        command_queue.put((command_data, result_queue))
        
        if isreturn == 1: #only look for a return value if isreturn = 1
            result = result_queue.get()
        else: result = 1
        
        return result 

# Client class to control a TMCL stepper motor (the commands are specific to this device...)
class MotorClient(): #i don't know if Thread is necessary
   
    def __init__(self, server, MODULE_ADDRESS, MOTOR_NUMBER, command_queue):  
   
        self.is_running = False  
        self.command_queue = command_queue
        
        #list might be adjusted if necessary
        self.command_functions = { 
            "start": self.start_motor,
            "stop": self.stop_motor,
            "stop_move": self.stop_move,
            "move_right": self.start_move_right,
            "move_left": self.start_move_left,
            "set_brake": self.set_brake,
            "release_brake": self.release_brake,
            "reference_search": self.reference_search,
            "go_to_position": self.goto_position,
            "get_position": self.get_position,
            "right_endstop": self.rightstop_status,
            "left_endstop": self.leftstop_status,
            "position_reached": self.position_reached,
            
        
        }
        
        
        self.stop_flag = threading.Event()
       
        self.server = server
       
        self.MODULE_ADDRESS = MODULE_ADDRESS 
       
        self.MOTOR_NUMBER = MOTOR_NUMBER
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
       
        #set initial position
        self.position = 0
       
    def start_motor(self):
        self.is_running = True
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
        self.motorconn = self.server.bus.get_motor(self.MODULE_ADDRESS,self.MOTOR_NUMBER) 
        self.axisparameter = AxisParameterInterface(self.motorconn)   #from allmyTMCLclasse; AxisParameterInterface
       
       
    def stop_motor(self):
        self.stop_flag.set()
        self.is_running= False
       
    def ex_command(self,command):
        """excecutes the commands which are sent by addressing the commands from the command list"""
        
        command_name, *args = command
       
        if command_name in self.command_functions:
            with serial_port_lock: #make sure that commands are only sent through the port if no other thread is using it already
                func = self.command_functions[command_name]
                func(*args)
    
    # def motor_functions(self, command):
    #        """should handle all possible commands and redirect them to the functions we have according to the keywords
    #            - either by using keywords or by using a numbers code"""
               
    #        print("hiiiii")
    #        command_name, *args = command
           
    #        print(command_name)
    #        print(*args)
    #        if command_name == "move_right":
    #            speed = args[0] if args else 1
    #            self.start_move_right(speed)
    #            #print(f"Motor {self.motor_id} moving right at speed {speed}")
    #        elif command_name == "move_left":
    #            speed = args[0] if args else 1
    #            #print(f"Motor {self.motor_id} moving left at speed {speed}")
    #        elif command_name == "stop":
    #            print("hello")
    #            self.stop_move()
    #           # print(f"Motor {self.motor_id} stopped")
    #        elif command_name == "set_brake":
    #            self.set_break()
    #           # print(f"Motor {self.motor_id} set brake")
    #        elif command_name == "release_brake":
    #            self.release_break()
    #        elif command_name == "reference_search":
    #            self.reference_search()
    #            #print(f"Motor {self.motor_id} performing reference search")
    #        elif command_name == "go_to_position":
    #            position = args[0] if args else self.get_position() #should remain at the same position if nothing is provided!!!
    #            self.goto_position(position)
    #        elif command_name == "get_speed":
    #            speed = self.get_speed()
    #            #print("momentary speed")
               
    def run(self):  
        """will keep running as soon as the thread is started and continuously checks for commands in the command queue.
        The commands in the command queue are issued from the """
        print(f"Motor is running on thread {threading.current_thread().name}")
        while self.is_running and not self.stop_flag.is_set():
            try:
                command, result_queue = self.command_queue.get_nowait() #waits for 1s unit to get an answer #get_nowait() #command should be of the format command = [command_name, *args]
                if command[0] == "get_position":
                    with serial_port_lock: #make sure that this function is also blocked
                        position = self.get_position()
                        if position is not None:
                            self.position = position
                            result_queue.put(position)
                if command[0] == "position_reached":
                      with serial_port_lock: #make sure that this function is also blocked
                          isreached = self.position_reached()
                          if isreached is not None:
                              result_queue.put(isreached)
                else:
                    #self.motor_functions(command)
                    self.ex_command(command)
            except queue.Empty:
                pass
            time.sleep(0.1) #just some waiting time here to keep synchronization 
            
            
    """commands are not similar enough to make effective use of set and get, however it will be more useful in EPICS version i think """
    # def set(self,param,value):
    #     command
    #     self.server.command_queue.put(command)
   
    # def get(self,param):
    #     self.motorconn.get_axis_parameter(param)
       
    def invalid_command(self):
        self.motorconn.send(234,0,2,1)

   
    def release_brake(self):
        self.motorconn.send(14,0,2,1) 
   
    def set_brake(self):
        self.motorconn.send(14,0,2,0)
       
    def start_move_left(self, speed):#this is backwards !!!
        self.motorconn.rotate_left(speed)
     
   
    def start_move_right(self, speed): #this is forwards !!!
        self.motorconn.rotate_right(speed)
       
 
    def stop_move(self):
        self.motorconn.stop()
        


    def goto_position(self,position):
        self.motorconn.move_absolute(position)
        
       
    def get_position(self):
        """TODO!!: return the position value. Define the LEFT endstop as "position 0"
        then count the revolutions for figuring out the actual position."""

        #51200 steps ~ 0.5 cm #not accurate...
        #10000 steps ~ 1.1 cm not accurate at all...
        onestep_incm = 1.1/100000 #0.5/51200
        numberofsteps = self.axisparameter.actual_position
        self.position = numberofsteps * onestep_incm
       
        leftend = 0
        rightend = 30 #measured by moving the sled there!!!
        
        if self.position <= leftend: #make sure the sled does not move beyond endstops!!!
            self.start_move_right(5000)
            time.sleep(1)
            self.stop_move()

        if self.position >= rightend:
            self.start_move_left(5000)
            time.sleep(1)
            self.stop_move()
       
        return self.position 
   
    def get_speed(self):
        speed = self.motorconn.get_axis_parameter(3)
        return speed
   
    def rightstop_status(self):
        return self.axisparameter.rightstop_readout()
       
    def leftstop_status(self):
        return self.axisparameter.leftstop_readout()
   
    def pps_to_rpm(self,v_pps): #standard values for a TMCL-1260
        """translate pulsepersecond to rev per minute"""
        v_rps = v_pps/(200*256)
        return 60*v_rps
   
    def position_reached(self):
        return self.motorconn.get_position_reached()
       
    def reference_search(self): #should of course be handled with interrupts but does not work for some reason...who can i ask...
        """move motor to the very left until endstop is triggered.
        Immediately stop and identify this position as '0'"""
        self.release_brake()
        self.start_move_left(15000) #just with some seed that is fast enough, left is backwards
        
       
        endstop = 0
        print("starting reference search")
        while endstop == 0: #check the endstop value and terminate as soon as it is 1
            endstop = self.rightstop_status() 
           
            time.sleep(0.1) 
       
        self.stop_move()
       
        time.sleep(0.2) #make sure it actually stopped
        self.set_brake()
        self.axisparameter.set(1,0)
        
        position = self.axisparameter.actual_position
        print("endstop position initialized as '0'")
        print("position:", position)
        return


    
if __name__ == "__main__": #is only excecuted if the program is started by itself and not if called by others, here for testing...
    try:
        # Initialize the server
        server = MotorServer(port='COM7', baud_rate=9600) #create the bus connection
        command_queue = queue.Queue() #create the command queue through which i will issue my motor commands, in the end i will have a queue for each motor
           
        MODULE_ADRESS = 1
        MOTOR_NUMBER = 0
           
        # Initialize the motor client and start it up in an extra thread.
        server.create_and_start_motor_client(server, MODULE_ADRESS, MOTOR_NUMBER, command_queue)

    except:
        print("thread error failed...")
    try:
        # Example: Move motor 1 by 1000 steps
       
        server.issue_motor_command(command_queue, ("release_brake",))
        
        server.issue_motor_command(command_queue, ("go_to_position",100000))
        #server.issue_motor_command(command_queue, ("move_right",20000))
        
        time.sleep(8)
        
        position = server.issue_motor_command(command_queue, ("get_position",), isreturn = 1)
        print(position)
        
        
        server.issue_motor_command(command_queue, ("stop_move",))
        server.issue_motor_command(command_queue, ("set_brake",))
        #command_queue.put(("stop_move",))
        #command_queue.put(("set_brake",))
       
       
        
        #command_queue.put(("stop",))
        server.issue_motor_command(command_queue, ("stop",))
        time.sleep(2) #give the thread some time before the connection is closed...
        server.stop_server() #stop server after series of commands, listening thread keeps running otherwise
       
    except KeyboardInterrupt:
        server.stop_server()
        print("KeyboardInterrupt, the server has stopped")