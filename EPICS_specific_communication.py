# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:45:18 2023

@author: silas
"""

import epics 
from epics import PV, camonitor
import threading
import queue 

import time




#Define a global lock for the serial port such that only one thread at a time can use it
serial_port_lock = threading.Lock() 

class MotorServer:
    def __init__(self, port, baud_rate):
       ...
     
       # self.serial_port = serial.Serial(port, baud_rate)
       # self.bus = connect(self.serial_port) #from AllpyTMCL_classes; init, this returns all methods form the Bus class, so we do not need any other method which "sends" directly to the serial port
       
    def send_command(self, command, value): 
        ...

   
    def stop_server(self): #make sure that when running it again the serial port is accessible
        self.running = False
        #self.serial_port.close()
        print(" closed")
       
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
            "set_speed": self.set_speed,
            "release_brake": self.release_brake,
            "reference_search": self.reference_search,
            "go_to_position": self.goto_position,
            "get_position": self.get_position,
            "right_endstop": self.endstop_status,
            "position_reached": self.position_reached,
            
        }
        
        
        self.stop_flag = threading.Event()
       
        self.server = server
       
        self.MODULE_ADDRESS = MODULE_ADDRESS 
       
        self.MOTOR_NUMBER = MOTOR_NUMBER
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
       
        #set initial position
        self.position = 0  #should be at zero and then i keep track of the position by using a stepcounter!
        self.stepcount = 0
       
        
        #keep track of movement for position
        self.ismoving = False
        self.direction = "pos" #default direction forward
        self.start_position_thread()
        
        #initialize the pv's i am using here 
        self.pv_brake = PV('XXX:m1.VAL') #change the names of record usw accordingly... prolly specific to the motor which is initialized ?
        self.pv_speed_set = PV('T-MWE1X:VL:1')
        self.pv_acc_set = PV('T-MWE1X:AC:1')
        self.pv_acc_get = PV('T-MWE1X:ACRB:1')
        self.pv_speed_get = PV('T-MWE1X:VLRB:1')
        self.pv_COM_status = PV('T-MWE1X:COM:2')
        self.pv_position = PV('XXX:m1.VAL')
        self.pv_targetposition_steps = PV('T-MWE1X:SOL:1') #in steps
        self.pv_rawincr_set = PV('T-MWE1X:INKR:raw')
        self.pv_targetreached = PV('XXX:m1.VAL')
        self.pv_endstopstatus = PV('T-MWE1X:STA:1') #a hex value which changes value according to which endstop that is being triggered
        self.pv_reference = PV('XXX:m1.VAL')
        
        #set an initial_speed to 500 steps/s
        self.Set(self.pv_speed_set,500)
    
       
    def start_motor(self):
        self.is_running = True
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
        self.motorconn = ...#self.server.bus.get_motor(self.MODULE_ADDRESS,self.MOTOR_NUMBER) 
        self.axisparameter = ... #AxisParameterInterface(self.motorconn)   #from allmyTMCLclasse; AxisParameterInterface
       
       
    def stop_motor(self):
        self.stop_flag.set()
        self.is_running= False
        print("stop")
       
    def ex_command(self,command):
        """excecutes the commands which are sent by addressing the commands from the command list"""
        
        command_name, *args = command
       
        if command_name in self.command_functions:
            with serial_port_lock: #make sure that commands are only sent through the port if no other thread is using it already
                func = self.command_functions[command_name]
                func(*args)
    
    
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
                #if command[0] == "go_to_position":
                   # self.ex_command(command) #excecute the command
                   # while self.ismoving == True:
                      #  time.sleep(0.05)
                    #Eresult_queue.put(self.ismoving)
                        
                else:
                    #self.motor_functions(command)
                    self.ex_command(command)
            except queue.Empty:
                pass
            time.sleep(0.1) #just some waiting time here to keep synchronization 
            
    
    def Set(self,pv,value):
        """sets the value of a passed process variable"""
        pv.put(value)
#     command
#     self.server.command_queue.put(command)

    def Get(self,pv):
        """gets the value of a passed process variable"""
        value = pv.get()
        return value
       

    def release_brake(self):
        self.Set(self.pv_brake,1)
   
    def set_brake(self):#there is no break at the moment
        self.Set(self.pv_brake,0)
       
    def start_move_left(self, steps_to_incr):#this is backwards !!!
        self.Set(self.pv_rawincr_set,-steps_to_incr) #negative to go left/backwards
     
   
    def start_move_right(self, steps_to_incr): #this is forwards !!!
        self.Set(self.pv_rawincr_set,steps_to_incr)
       
 
    def stop_move(self):
        self.Set(self.pv_speed_set,0)


    def goto_position(self,position_steps):
        #position_steps = self.position_to_steps(position)
        print("here")
        if position_steps > 0:
            self.direction = "pos"
        if position_steps < 0: 
            self.direction = "neg"
        self.Set(self.pv_targetposition_steps, position_steps)
        self.ismoving = True #maybe this is it...
        velocity = self.Get(self.pv_speed_get)
        
        print("velocity", velocity)
        
        if velocity != 0:
            time_needed = abs(self.stepcount - position_steps)/velocity 
        else:
            time_needed = 0.01
            print("WARNING: velocity is 0")
        print("time needed", time_needed)
        
        time.sleep(time_needed) #wait with other commands during that time as well
        
        self.stepcount = self.stepcount + position_steps
        print("stepcount is:", self.stepcount)
        self.ismoving = False
        
        return
       
    def get_position(self):
        """ return the position value. Define the LEFT endstop as "position 0"
        then count the revolutions for figuring out the actual position."""
        
        return self.position  #this value is adjusted by the other functions
   
    def set_speed(self,speed):
        self.Set(self.pv_speed_set,speed)
    
    def get_speed(self):
        speed = self.Get(self.pv_speed_get)
        return speed
   
    def endstop_status(self):
        endstopvalue = self.Get(self.pv_endstopstatus)
        
        if endstopvalue == 0xD:
            print("upper end reached")
            return "upper"
        if endstopvalue == 0xB:
            print("lower end reached")
            return "lower"
        else:
            print("no endstop reached")
            return None
        
            
    def position_reached(self):
        """returns True or False, maybe do it by using the 'busy' PV """
        ...
        #return self.Get(self.pv_targetreached)
       
    def reference_search(self): #should of course be handled with interrupts but does not work for some reason...who can i ask...
        """move motor to the very left until endstop is triggered.
        Immediately stop and identify this position as '0'"""
        self.release_brake()  #prolly won't do much
        self.start_move_left(50000) #start to move a big value until the endstop is reached, stops automatically
    
        endstop = None
        print("starting reference search")
        while endstop == None: #check the endstop value and terminate as soon as it is 1
            endstop = self.endstop_status() 
        self.stop_move()
       
        #time.sleep(0.2) #make sure it actually stopped
        self.set_brake()
        #self.axisparameter.set(1,0)
        
        #position = self.axisparameter.actual_position
        print("endstop position initialized as '0'")
        self.stepcount = 0
        #print("position:", position)
        return


    
    def move_device_position(self):
        
        while True:
            #print(self.ismoving)
    
            if self.ismoving:
                
                velocity = self.Get(self.pv_speed_get)
                acceleration = self.Get(self.pv_acc_get)
                
                
                looptime = 0.1
                if self.direction == "pos":
                    self.position +=  velocity*looptime
                if self.direction == "neg":
                    self.position -= velocity*looptime
                print(self.position)
            time.sleep(0.1)  # Adjust the sleep time as needed

    def start_position_thread(self):
        print("istarted")
        self.thread = threading.Thread(target=self.move_device_position)
        self.thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        self.thread.start()

    def stop_position_thread(self):
        self.ismoving = False
        self.thread.join()




    
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
       
        #server.issue_motor_command(command_queue, ("release_brake",))
        
        #server.issue_motor_command(command_queue, ("reference_search",))
        
        server.issue_motor_command(command_queue, ("go_to_position",1000))
        
        #server.issue_motor_command(command_queue, ("move_left", 5000))
        #server.issue_motor_command(command_queue, ("move_right",20000))
        
        time.sleep(5)
        
        position = server.issue_motor_command(command_queue, ("get_position",), isreturn = 1)
        print(position)
        
        
        #server.issue_motor_command(command_queue, ("stop_move",))
        #server.issue_motor_command(command_queue, ("set_brake",))
        #command_queue.put(("stop_move",))
        #command_queue.put(("set_brake",))
       
       
        
        #command_queue.put(("stop",))
        server.issue_motor_command(command_queue, ("stop",))
        time.sleep(2) #give the thread some time before the connection is closed...
        server.stop_server() #stop server after series of commands, listening thread keeps running otherwise
       
    except KeyboardInterrupt:
        server.stop_server()
        print("KeyboardInterrupt, the server has stopped")