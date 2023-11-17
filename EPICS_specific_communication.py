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




#Define a global lock for the port such that only one thread at a time can use it
#port_lock = threading.Lock() 

class MotorServer:
    def __init__(self):
       self.running = True
       self.pv_status = PV('MTEST-WA81-VME02:ES:SBNT')
    def stop_server(self): #make sure that when running it again the port is accessible
        self.running = False
        
        print(" closed")
        
       
    def start(self): #sends everything that is put into the queue
        try:
            while self.running:
                print("is reading:", self.isreading)
                if not self.command_queue.empty():# and self.isreading:
                    print("is reading:", self.isreading)
                    command = self.command_queue.get() #command_item = self.command_queue.get()#
                  
                    self.send_command(command)
                   

                    
        except KeyboardInterrupt:
            self.serial_port.close()
            print("Exiting...")
    
    def create_and_start_motor_client(self,server, MOTOR_NUMBER, command_queue):
        motor = MotorClient(server, MOTOR_NUMBER, command_queue) #pass the general port lock to each motor thread
        motor.start_motor()
        thread = threading.Thread(target=motor.run)
        thread.start()
        return motor

    def issue_motor_command(self,motor,command_data, isreturn = 0):
        self.issending = True
        result_queue = queue.Queue()
        
        motor.command_queue.put((command_data, result_queue)) #put the command in the queue regardless
    
        if isreturn == 1: #only look for a return value if isreturn = 1
            result = result_queue.get()
        else: result = 1
    
        return result 

# Client class to control a TMCL stepper motor (the commands are specific to this device...)
class MotorClient(): #i don't know if Thread is necessary
   
    def __init__(self, server, MOTOR_NUMBER, command_queue):  
   
        self.initializing = True 
        #self.port_lock = threading.Lock() #create a lock for each motor such that i can't do someting with the motor while it is locked
        
        self.is_running = False  
        self.command_queue = command_queue
        
        #list might be adjusted if necessary
        self.command_functions = { 
            "start": self.start_motor,
            "stop": self.stop_motor,
            "stop_move": self.stop_move,
            "move_forwards": self.move_forwards,
            "move_backwards": self.move_backwards,
            "set_brake": self.set_brake,
            "set_speed": self.set_speed,
            "get_speed": self.get_speed,
            "release_brake": self.release_brake,
            "reference_search": self.reference_search,
            "go_to_position": self.goto_position,
            "get_position": self.get_position,
            "right_endstop": self.endstop_status,
            "position_reached": self.position_reached,
            "calibrate": self.calibration,
            
        }
        
        
        self.stop_flag = threading.Event()
       
        self.server = server
       
        self.MOTOR_NUMBER = MOTOR_NUMBER
        #get the motorconn at address 1 motor 0 (the only one available at the moment) later there might be three axis i.e. motor can be 0,1,2
       
        #set initial position
        self.position = 0  #should be at zero and then i keep track of the position by using a stepcounter!
        self.stepcount = 0
        self.time_needed = 0
        
        #keep track of movement for position
        self.iscalibrating = False
        self.ismoving = False
        self.direction = "pos" #default direction forward
        self.start_position_thread()
        
        #start the thread to time ismoving variable...
        self.start_timer_thread()
        
        self.locked = False
        #depending on MOTOR_NUMBER this will be different
        
        
        
        if MOTOR_NUMBER == 1:
            #initialize the pv's i am using here 
            #with self.port_lock:
                
                
                self.pv_CMD_status = PV('T-MWE1X:CMDS:1:SBNT') #command status, if 0 then busy
                self.pv_brake = PV('XXX:m1.VAL') #has none
                self.pv_speed_set = PV('T-MWE1X:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE1X:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE1X:DIST:2')
                self.pv_ramp_set = PV('T-MWE1X:SMRAMP:2')
                self.pv_speed_get = PV('T-MWE1X:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE1X:COM:2')
                self.pv_position = PV('T-MWE1X:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE1X:SOL:1') #in steps
                self.pv_move_rel = PV('T-MWE1X:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE1X:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE1X:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_emstop = PV('T-MWE1X:STOP:2')
                self.pv_command = PV('T-MWE1X:CMD:2')
                self.pv_MAXCW = PV('T-MWE1X:MAXCW:2')
                self.pv_SPAD = PV('T-MWE1X:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE1X:SOL:1.DRVL')
                self.pv_targetposition_DRVH = PV('T-MWE1X:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE1X:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE1X:SOL:1.HOPR')
                
                #set initial parameters and calibrate
                self.calibration() #i do calibrate!!!
                self.pv_speed_set.put(1500)
                self.pv_min_speed_set.put(500)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(25)
                #print(self.pv_speed_set.get())
                self.pv_MAXCW.put(21766)
                self.pv_SPAD.put(752) #don't part. about this value...
                
                self.pv_targetposition_DRVL.put(-10) #check what happens
                self.pv_targetposition_DRVH.put(21766)
                self.pv_targetposition_LOPR.put(-10)
                self.pv_targetposition_HOPR.put(21766)
            
            
        if MOTOR_NUMBER == 2: #correct PV's
            #initialize the pv's i am using here 
           # with self.port_lock:
                self.pv_CMD_status = PV('T-MWE1Y:CMDS:1:SBNT') #command status, if 0 then busy
                self.pv_brake = PV('XXX:m1.VAL') #has none
                self.pv_speed_set = PV('T-MWE1Y:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE1Y:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE1Y:DIST:2')
                self.pv_ramp_set = PV('T-MWE1Y:SMRAMP:2')
                self.pv_speed_get = PV('T-MWE1Y:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE1Y:COM:2')
                self.pv_position = PV('T-MWE1Y:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE1Y:SOL:1') #in steps
                self.pv_move_rel = PV('T-MWE1Y:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE1Y:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE1Y:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_emstop = PV('T-MWE1Y:STOP:2')
                self.pv_command = PV('T-MWE1Y:CMD:2')
                self.pv_MAXCW = PV('T-MWE1Y:MAXCW:2')
                self.pv_SPAD = PV('T-MWE1Y:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE1Y:SOL:1.DRVL') #endpoint parameters for SOL:1
                self.pv_targetposition_DRVH = PV('T-MWE1Y:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE1Y:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE1Y:SOL:1.HOPR')
                
                self.calibration()
                self.pv_speed_set.put(1500)
                self.pv_min_speed_set.put(500)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(25)
                #print(self.pv_speed_get.get())
                self.pv_MAXCW.put(104172)  
                self.pv_SPAD.put(752) #don't part. about this value...
            

                self.pv_targetposition_DRVL.put(-10)
                self.pv_targetposition_DRVH.put(104172)
                self.pv_targetposition_LOPR.put(-10)
                self.pv_targetposition_HOPR.put(104172)
            
        if MOTOR_NUMBER == 3: #correct PV's
            #initialize the pv's i am using here 
            #with self.port_lock:
                self.pv_CMD_status = PV('T-MWE2Y:CMDS:1:SBNT') #command status, if 0 then busy
                self.pv_brake = PV('T-MWE2Y:CMD2-BRAKE:2') #has a break... extra cable... not known yet
                self.pv_brake_status = PV('T-MWE2Y:CMD2-BRAKERB:2')
                self.pv_speed_set =  PV('T-MWE2Y:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE2Y:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE2Y:DIST:2')
                self.pv_ramp_set = PV('T-MWE2Y:SMRAMP:2')
                self.pv_speed_get =  PV('T-MWE2Y:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE2Y:COM:2')
                self.pv_position = PV('T-MWE2Y:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE1X:SOL:1') #in steps
                self.pv_move_rel = PV('T-MWE2Y:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE2Y:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE2Y:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_emstop = PV('T-MWE2Y:STOP:2')
                self.pv_command = PV('T-MWE2Y:CMD:2')
                self.pv_MAXCW = PV('T-MWE2Y:MAXCW:2')
                self.pv_SPAD = PV('T-MWE2Y:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE2Y:SOL:1.DRVL')
                self.pv_targetposition_DRVH = PV('T-MWE2Y:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE2Y:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE2Y:SOL:1.HOPR')
                
                self.calibration()
                self.pv_brake.put(1)
                self.pv_speed_set.put(1500)
                self.pv_min_speed_set.put(500)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(25)
                #print(self.pv_speed_set.get())
                #time.sleep(0.1)
                self.pv_MAXCW.put(9600)  
                self.pv_SPAD.put(752) #don't part. about this value...
                
                self.pv_targetposition_DRVL.put(-10)
                self.pv_targetposition_DRVH.put(9600)
                self.pv_targetposition_LOPR.put(-10)
                self.pv_targetposition_HOPR.put(9600)
            
        self.initializing = False
       
    def start_motor(self):
        self.is_running = True
        #not necessary anymore as long as python script run in same place as EPICS does --> PV's are visible then
        #self.motorconn = ...#self.server.bus.get_motor(self.MODULE_ADDRESS,self.MOTOR_NUMBER) 
        #self.axisparameter = ... #AxisParameterInterface(self.motorconn)   #from allmyTMCLclasse; AxisParameterInterface
       
       
    def stop_motor(self):
        self.stop_flag.set()
        self.is_running = False
        self.stop_position_thread()
        
        print("stop")
       
    def ex_command(self,command):
        """excecutes the commands which are sent by addressing the commands from the command list"""
        
        command_name, *args = command
       
        if command_name in self.command_functions:
            #with port_lock: #make sure that commands are only sent through the port if no other thread is using it already
                func = self.command_functions[command_name]
                func(*args)
        return "done"
    def run(self):  
        """will keep running as soon as the thread is started and continuously checks for commands in the command queue.
        The commands in the command queue are issued from the """
        print(f"Motor is running on thread {threading.current_thread().name}")
        while self.is_running and not self.stop_flag.is_set():
             #make sure that this critical section can only be accessed when the motor lock is free
                try:
                    if self.Get(server.pv_status) != 1 and self.Get(self.pv_CMD_status) != 0: #should be 0 :()
                    
                        command, result_queue = self.command_queue.get_nowait() #waits for 1s unit to get an answer #get_nowait() #command should be of the format command = [command_name, *args]
                        if command[0] == "get_position":
                            #with port_lock: #make sure that this function is also blocked
                                position = self.get_position()
                                if position is not None:
                                    self.position = position
                                    result_queue.put(position)
                                    res = "done"
                        if command[0] == "position_reached":
                              #with port_lock: #make sure that this function is also blocked
                                  isreached = self.position_reached()
                                  if isreached is not None:
                                      result_queue.put(isreached)
                                      res = "done"
                        #if command[0] == "go_to_position":
                           # self.ex_command(command) #excecute the command
                           # while self.ismoving == True:
                              #  time.sleep(0.05)
                            #Eresult_queue.put(self.ismoving)
                        if command[0] == "get_speed":
                            #with port_lock: #make sure that this function is also blocked
                                speed = self.get_speed()
                                result_queue.put(speed)
                                res = "done"
                        else:
                            print("else")
                            res = self.ex_command(command)
                        
                        if res == "done":
                            self.server.issending = False
                            time.sleep(0.1)
                            print("free again")
                    else:
                        print("is busy, try again later")
                        print(self.Get(server.pv_status))
                        print(self.Get(self.pv_CMD_status))
                        
                        #time.sleep(0.2)
                    
                except:
                        if self.command_queue.empty():
                            pass
                        else: print("something worse happened")
                    
            
            
    
    def Set(self,pv,value):
        """sets the value of a passed process variable"""
        #with self.port_lock:
        print("set")
        pv.put(value)
        #time.sleep(0.2) #safety
        return "has been set"

    def Get(self,pv):
        """gets the value of a passed process variable"""
        #with self.port_lock:
        value = pv.get()
        return value
       

    def release_brake(self):
        self.Set(self.pv_brake,1) #or reversed...
   
    def set_brake(self):
        self.Set(self.pv_brake,0)
       
    def move_backwards(self, steps_to_incr):#this is backwards !!!
        self.Set(self.pv_rawincr_set,-steps_to_incr) #negative to go left/backwards
     
   
    def move_forwards(self, steps_to_incr): #this is forwards !!!
        self.Set(self.pv_rawincr_set,steps_to_incr)
       
 
    def stop_move(self):
        self.Set(self.pv_speed_set,0)


    def goto_position(self,position_steps):
        #position_steps = self.position_to_steps(position)
        #with self.port_lock:
            print(position_steps)
            if position_steps > 0:
                self.direction = "pos"
            if position_steps < 0: 
                self.direction = "neg"
            
            velocity = self.Get(self.pv_speed_get)
            
            print("velocity", velocity)
            
            while self.ismoving == True:
                print("waiting")
                time.sleep(0.1)
            
            if velocity !=0 and velocity!= None:
                time.sleep(1) #safety wait because otherwise the processing has not yet been done...
                res = self.Set(self.pv_targetposition_steps, position_steps) #making sure it has actually been sent befor the waiting time
                print(res)
                self.ismoving = True 
                self.time_needed = abs(self.stepcount - position_steps)/velocity  
                
        
                self.stepcount = position_steps #new position in steps #SOL position
                print("stepcount is:", self.stepcount)  
                print("time needed", self.time_needed)
            else:
                self.ismoving = True
                print("WARNING: velocity is 0 or None")
                self.time_needed = 3
                #self.start_timer_thread(time_needed)
        
         #wait with other commands during that time as well
    
            #self.ismoving = False
        
            return
       
      
    def get_position(self):
        """ return the position value. Define the LEFT endstop as "position 0"
        then count the revolutions for figuring out the actual position."""
        
        return self.position  #this value is adjusted by the other functions
   
    def set_speed(self,speed):
        self.Set(self.pv_speed_set, speed)
        # with self.port_lock:
        #     self.pv_speed_set.put(speed)
        
    
    def get_speed(self):
        
        speed = self.Get(self.pv_speed_get)
        return speed
   
    def endstop_status(self):
        #to do
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
       
        
    def calibration(self):
        if self.Get(self.pv_speed_get) == None:
            return
        self.Set(self.pv_command,1) #enumerated calCCW to 1 i think 
        self.iscalibrating = True
        #time.sleep(0.2)
        while self.Get(self.pv_endstopstatus) != 0xD: #didn't reach endstop ye
             #print(self.Get(self.pv_endstopstatus))
             time.sleep(0.1)
        self.iscalibrating = False
        print("done calibrating")
        
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
                #print(velocity)
                if velocity != None:
                    looptime = 0.1
                    if self.direction == "pos":
                        self.position +=  velocity*looptime
                    if self.direction == "neg":
                        self.position -= velocity*looptime
                #print(self.position)
            time.sleep(0.1)  # Adjust the sleep time as needed

        self.ismoving = False
        
    def lock_for_time(self):
        while True:
            
            if self.time_needed > 0:  #only when it has been set true in another place!!!
                start = time.time()
                print("start counting")
                while time.time() - start < self.time_needed:
                    pass
                print("ended, reset ismoving and time_needed")
                self.ismoving = False
                self.time_needed = 0 
                
                #self.thread.join()
            #self.stop_timer_thread()
        
    def start_position_thread(self):
        print("position thread")
        self.thread = threading.Thread(target=self.move_device_position)
        self.thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        self.thread.start()

    def stop_position_thread(self):
        self.ismoving = False
        print("stopped moving")
        self.thread.join()

    def start_timer_thread(self):
        print("timer thread")
        self.thread = threading.Thread(target=self.lock_for_time)
        self.thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        self.thread.start()
        
    def stop_timer_thread(self):
        self.thread.join()



    
if __name__ == "__main__": #is only excecuted if the program is started by itself and not if called by others, here for testing...
    #try:
        # Initialize the server
        server = MotorServer()
        command_queue = queue.Queue() #create the command queue through which i will issue my motor commands, in the end i will have a queue for each motor
        command_queue2 = queue.Queue()
        
        MOTOR_NUMBER = 1
           
        # Initialize the motor client and start it up in an extra thread.
        
        motor1 = server.create_and_start_motor_client(server, MOTOR_NUMBER, command_queue)
        #time.sleep(2)
        motor2 = server.create_and_start_motor_client(server, 2, command_queue2)
        
        print("cmdstatus of 2 is", motor2.Get(motor2.pv_CMD_status))
        print("cmdstatus of 1 is", motor2.Get(motor1.pv_CMD_status))
        
        while motor1.initializing == True or motor2.initializing == True: 
            time.sleep(0.1)
        #time.sleep(10)
        print("done initializing")
    
    #except:
        #print("thread error failed...")
    #try:
        
        # Example: Move motor 1 by 1000 steps
        #server.issue_motor_command(motor2, ("calibrate",))
        #server.issue_motor_command(motor1, ("calibrate",))
        # time.sleep(0.1)
        # while motor3.iscalibrating == True: #or motor3.iscalibrating == True: #wait for calibration to be done
        #     time.sleep(0.1)
        #     print("calibrating")
        # server.issue_motor_command(motor1, ("set_speed",1500))
        # server.issue_motor_command(motor2, ("set_speed",1500)) 
        #time.sleep(0.2)
        #erver.issue_motor_command(motor1, ("set_speed",1300))
        #print("here")
        
        
        #server.issue_motor_command(motor1, ("go_to_position",1000)) #do not return from this;((()))
        server.issue_motor_command(motor2, ("go_to_position",2000))
        #time.sleep(0.2)
        server.issue_motor_command(motor1, ("go_to_position",2000))
        #time.sleep(0.2)
       #  server.issue_motor_command(motor1, ("go_to_position",1))
       # # time.sleep(0.2)
       #  #server.issue_motor_command(motor1, ("go_to_position",0))
       #  #time.sleep(1)
       #  server.issue_motor_command(motor2, ("go_to_position",1))
        #time.sleep(0.2)
        #server.issue_motor_command(motor1, ("go_to_position",2000))
        # server.issue_motor_command(motor1, ("go_to_position",1000))
        # server.issue_motor_command(motor2, ("go_to_position",1000))
        
        server.issue_motor_command(motor1, ("go_to_position",0))
        server.issue_motor_command(motor2, ("go_to_position",0))
        #server.issue_motor_command(motor2, ("calibrate",))
        #server.issue_motor_command(motor1, ("calibrate",))
        # server.issue_motor_command(motor1, ("go_to_position",1100))
        # server.issue_motor_command(motor2, ("go_to_position",1100))
        
        
        
        # server.issue_motor_command(motor2, ("go_to_position",0))#this command is lost when the one before took too long
        
        # server.issue_motor_command(motor1, ("go_to_position",0))
        
        # server.issue_motor_command(motor1, ("go_to_position",100))
        
        # server.issue_motor_command(motor2, ("go_to_position",100))
        
        
        
        #server.issue_motor_command(command_queue, ("move_left", 5000))
        #server.issue_motor_command(command_queue, ("move_right",20000))
        
        # time.sleep(0.1)
        
        # speed = server.issue_motor_command(motor1, ("get_speed",), isreturn = 1)
        # print(speed)
        
        
        #server.issue_motor_command(command_queue, ("stop_move",))
        #server.issue_motor_command(command_queue, ("set_brake",))
        #command_queue.put(("stop_move",))
        #command_queue.put(("set_brake",))
       
       
        
        #command_queue.put(("stop",))
        #server.issue_motor_command(command_queue, ("stop",))
        #time.sleep(30) #give the thread some time before the connection is closed...
        server.stop_server() #stop server after series of commands, listening thread keeps running otherwise
       
    #except KeyboardInterrupt:
        #server.stop_server()
        #print("KeyboardInterrupt, the server has stopped")