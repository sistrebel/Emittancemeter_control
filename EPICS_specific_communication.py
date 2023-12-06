# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:45:18 2023

@author: silas
"""

import epics 
from epics import PV, camonitor,caget
import threading
import queue 
from multiprocessing import Manager

import numpy as np
import time
import datetime
import scan_script as scan

import Calculate_emittance 

#Define a global lock for the port such that only one thread at a time can use it
#port_lock = threading.Lock() 

class MotorServer:
    def __init__(self):
       self.running = True
       self.pv_status = PV('MTEST-WA81-VME02:ES:SBNT')
       self.issending = False
       
       #necessary status variables to ensure proper running. For example a boolean which checks if the voltage is applied.
       
    
    def stop_server(self): #make sure that when running it again the port is accessible
        self.running = False
        print(" closed")
        
    def create_and_start_motor_client(self,server, MOTOR_NUMBER, command_queue):
        motor = MotorClient(server, MOTOR_NUMBER, command_queue) #pass the general port lock to each motor thread
        motor.start_motor()
        thread = threading.Thread(target=motor.run)
        thread.daemon = True
        thread.start()
        return motor

    def issue_motor_command(self,motor,command_data, isreturn = 0):
        """puts a command which comes from anywhere with access to this "server" into the command queue of the particular motor"""
        self.issending = True
        result_queue = queue.Queue()
        
        motor.command_queue.put((command_data, result_queue)) #put the command in the queue regardless
    
        if isreturn == 1: #only look for a return value if isreturn = 1
            result = result_queue.get()
        else: result = 1
    
        return result 


class MotorClient(): 
    """Client class to control a stepper motor contorlled by a series of EPICS process variables
    class MotorClient(): """
    def __init__(self, server, MOTOR_NUMBER, command_queue):  
        
        self.MOTOR_NUMBER = MOTOR_NUMBER
        
        self.initializing = True 
        
        self.is_running = False  
        
        self.command_queue = command_queue
        
        #list might be adjusted if necessary
        self.command_functions = { 
            "start": self.start_motor,
            "stop": self.stop_motor,
            # "stop_move": self.stop_move,
            # "move_forwards": self.move_forwards,
            # "move_backwards": self.move_backwards,
            "set_brake": self.set_brake,
            "set_speed": self.set_speed,
            "get_speed": self.get_speed,
            "release_brake": self.release_brake,
            # "reference_search": self.reference_search,
            "go_to_position": self.goto_position,
            "get_position": self.get_position,
            "right_endstop": self.endstop_status,
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
    

        self.locked = False
    
    
        
        if MOTOR_NUMBER == 1:
            #initialize the pv's i am using here 

                self.pv_CHS_SBNT = PV('T-MWE1X:CHS:1:SBNT')
                self.pv_CMD_status = PV('T-MWE1X:CMDS:1:SBNT') #command status, if 0 then busy
                self.pv_motor_status = PV('T-MWE1X:CHS:1') #motor status!!!
                self.pv_brake = PV('XXX:m1.VAL') #has none
                self.pv_speed_set = PV('T-MWE1X:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE1X:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE1X:DIST:2')
                self.pv_ramp_set = PV('T-MWE1X:SMRAMP:2')
                self.pv_speed_get = PV('T-MWE1X:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE1X:COM:2')
                self.pv_position = PV('T-MWE1X:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE1X:SOL:1') #in steps
                self.pv_SOLRB = PV('T-MWE1X:SOLRB:1')
                self.pv_move_rel = PV('T-MWE1X:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE1X:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE1X:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_stopstatus = PV('T-MWE1X:STOP:2')
                self.pv_command = PV('T-MWE1X:CMD:2')
                self.pv_MAXCW = PV('T-MWE1X:MAXCW:2')
                self.pv_SPAD = PV('T-MWE1X:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE1X:SOL:1.DRVL')
                self.pv_targetposition_DRVH = PV('T-MWE1X:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE1X:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE1X:SOL:1.HOPR')
                
                #set initial parameters and calibrate
               
                #self.calibration() #i do calibrate!!!
    
                self.pv_speed_set.put(1500)
                self.pv_min_speed_set.put(500)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(25)
                self.pv_MAXCW.put(21766)
                #self.pv_SPAD.put(752) #don't part. about this value...
                
                self.pv_targetposition_DRVL.put(0) #check what happens
                self.pv_targetposition_DRVH.put(21766)
                self.pv_targetposition_LOPR.put(0)
                self.pv_targetposition_HOPR.put(21766)
                
        if MOTOR_NUMBER == 2: #correct PV's
            #initialize the pv's i am using here 
                self.pv_CHS_SBNT = PV('T-MWE1Y:CHS:1:SBNT')
                self.pv_CMD_status = PV('T-MWE1Y:CMDS:1:SBNT') #command status, if 0 then busy
                self.pv_motor_status = PV('T-MWE1Y:CHS:1')
                self.pv_brake = PV('XXX:m1.VAL') #has none
                self.pv_speed_set = PV('T-MWE1Y:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE1Y:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE1Y:DIST:2')
                self.pv_ramp_set = PV('T-MWE1Y:SMRAMP:2')
                self.pv_speed_get = PV('T-MWE1Y:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE1Y:COM:2')
                self.pv_position = PV('T-MWE1Y:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE1Y:SOL:1') #in steps
                self.pv_SOLRB = PV('T-MWE1Y:SOLRB:1')
                self.pv_move_rel = PV('T-MWE1Y:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE1Y:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE1Y:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_stopstatus = PV('T-MWE1Y:STOP:2')
                self.pv_command = PV('T-MWE1Y:CMD:2')
                self.pv_MAXCW = PV('T-MWE1Y:MAXCW:2')
                self.pv_SPAD = PV('T-MWE1Y:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE1Y:SOL:1.DRVL') #endpoint parameters for SOL:1
                self.pv_targetposition_DRVH = PV('T-MWE1Y:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE1Y:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE1Y:SOL:1.HOPR')
                
                #self.calibration()
                self.pv_speed_set.put(1500)
                self.pv_min_speed_set.put(500)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(25)
                self.pv_MAXCW.put(104172)  
                #self.pv_SPAD.put(752) #don't part. about this value...
            

                self.pv_targetposition_DRVL.put(0)
                self.pv_targetposition_DRVH.put(104172)
                self.pv_targetposition_LOPR.put(0)
                self.pv_targetposition_HOPR.put(104172)
                
            
        if MOTOR_NUMBER == 3: #correct PV's
            #initialize the pv's i am using here 
                
                self.pv_command_status = PV('T-MWE2Y:CMDE:1')
                self.pv_CHS_SBNT = PV('T-MWE2Y:CHS:1:SBNT')
                self.pv_CMD_status = PV('T-MWE2Y:CMDS:1:SBNT') #command status, if 0 then busy...can't be used...
                self.pv_motor_status = PV('T-MWE2Y:CHS:1')
                self.pv_brake = PV('T-MWE2Y:CMD2-BRAKE:2') #has a break... extra cable... not known yet
                self.pv_brake_status = PV('T-MWE2Y:CMD2-BRAKERB:2')
                self.pv_brake_on = PV('T-MWE2Y:CMD2-BRON:2')
                self.pv_brake_off = PV('T-MWE2Y:CMD2-BROFF:2')
                self.pv_speed_set =  PV('T-MWE2Y:SMMAX:2')
                self.pv_min_speed_set = PV('T-MWE2Y:SMMIN:2')
                self.pv_speed_dist = PV('T-MWE2Y:DIST:2')
                self.pv_ramp_set = PV('T-MWE2Y:SMRAMP:2')
                self.pv_speed_get =  PV('T-MWE2Y:SMMAXRB:2')
                self.pv_COM_status = PV('T-MWE2Y:COM:2')
                self.pv_position = PV('T-MWE2Y:IST:1')  #in steps
                self.pv_targetposition_steps = PV('T-MWE2Y:SOL:1') #in steps
                self.pv_SOLRB = PV('T-MWE2Y:SOLRB:1')
                self.pv_move_rel = PV('T-MWE2Y:SMMS:2') #move relative 
                self.pv_move_abs = PV('T-MWE2Y:SMAP:2') #move absolute
                self.pv_targetreached = PV('XXX:m1.VAL')
                self.pv_endstopstatus = PV('T-MWE2Y:STA:1') #a hex value which changes value according to which endstop that is being triggered
                self.pv_stopstatus = PV('T-MWE2Y:STOP:2')
                self.pv_command = PV('T-MWE2Y:CMD:2')
                self.pv_MAXCW = PV('T-MWE2Y:MAXCW:2')
                self.pv_SPAD = PV('T-MWE2Y:SPAD:2')
                self.pv_targetposition_DRVL = PV('T-MWE2Y:SOL:1.DRVL')
                self.pv_targetposition_DRVH = PV('T-MWE2Y:SOL:1.DRVH')
                self.pv_targetposition_LOPR = PV('T-MWE2Y:SOL:1.LOPR')
                self.pv_targetposition_HOPR = PV('T-MWE2Y:SOL:1.HOPR')
                
                self.pv_brake.put(1) #make sure it is set right...
                while self.Get(self.pv_brake_status) != 1:
                    print("setting brake")
                    self.pv_brake.put(1)
                    time.sleep(0.1)
               
                
                
              
                self.pv_speed_set.put(1000)
                self.pv_min_speed_set.put(0)
                self.pv_speed_dist.put(200)
                self.pv_ramp_set.put(350) #long enough ramp
                self.pv_brake_off.put(500) #time before busy 
                self.pv_brake_on.put(300) #time after busy
                
                self.pv_MAXCW.put(9600)  
                #self.pv_SPAD.put(752) #don't part. about this value...
                
                self.pv_targetposition_DRVL.put(0)
                self.pv_targetposition_DRVH.put(9600)
                self.pv_targetposition_LOPR.put(0)
                self.pv_targetposition_HOPR.put(9600)
                
                #self.calibration()
                
                time.sleep(0.5)
        if self.iscalibrating == False:
            self.initializing = False
            
        self.start_timer_thread()
       
    def start_motor(self):
        self.is_running = True
        
       
    def stop_motor(self):
        self.stop_flag.set()
        self.is_running = False
        self.stop_position_thread()
        print("stop")
       
    def ex_command(self,command):
        """excecutes the commands which are sent by addressing the commands from the command list which then calls the functions to execute the commands"""
        command_name, *args = command
        if command_name in self.command_functions:
                func = self.command_functions[command_name]
                func(*args)
        return "done"
    def run(self):  
        """will keep running as soon as the thread is started and continuously checks for commands in the command queue.
        The commands in the command queue are issued from the """
        
        print(f"Motor is running on thread {threading.current_thread().name}")
        while self.is_running and not self.stop_flag.is_set():
                if not self.server.running:
                    break
                try:
                    status = self.pv_motor_status.get()
                    if status == 0x9 or status == 0x8 or status == 0xA or status == 0x1 or status == 0x0 and self.Get(self.server.pv_status) != 1  : 
                    
                        command, result_queue = self.command_queue.get_nowait() #waits for 1s unit to get an answer #get_nowait() #command should be of the format command = [command_name, *args]
                     
                        #if command[0] == "go_to_position":
                           # self.ex_command(command) #excecute the command
                           # while self.ismoving == True:
                              #  time.sleep(0.05)
                            #Eresult_queue.put(self.ismoving)
                        if command[0] == "get_speed":
                                speed = self.get_speed()
                                result_queue.put(speed)
                                res = "done"
                        else:
                            print("else")
                            res = self.ex_command(command)
                            res = "done"
            
                        if res == "done":
                            self.server.issending = False
                            print("free again")
                    
                    else: pass

                except:
                        if self.command_queue.empty():
                            pass
                        else: 
                            print("closed the application")
                    
            
        
    def Set(self,pv,value):
        """sets the value of a passed process variable"""
        print("set")
        pv.put(value)
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
       
    # def move_backwards(self, steps_to_incr):#this is backwards !!!
    #     self.Set(self.pv_rawincr_set,-steps_to_incr) #negative to go left/backwards
     
   
    # def move_forwards(self, steps_to_incr): #this is forwards !!!
    #     self.Set(self.pv_rawincr_set,steps_to_incr)
       
 
    # def stop_move(self):
    #     self.Set(self.pv_speed_set,0)


    def goto_position(self,position_steps):
            """moves the motor to the desired position specified by position_steps
            determines the direction of movement and checks if the velocity is 0"""
            if position_steps > self.stepcount:
                self.direction = "pos"
            if position_steps < self.stepcount: 
                self.direction = "neg"
            if position_steps == self.stepcount:
                self.direction = "none"
            
            
            velocity = self.pv_speed_get.get() #self.Get(self.pv_speed_get)
            
            print("velocity", velocity)
            
            # while self.ismoving == True:
            #     print("waiting")
            #     time.sleep(0.1)
            
            if velocity !=0 and velocity!= None:
                self.Set(self.pv_targetposition_steps, position_steps) #making sure it has actually been sent befor the waiting time
                print(" i am here")
                self.ismoving = True 
                self.time_needed = abs(self.stepcount - int(position_steps))/velocity  
                
        
                self.stepcount = position_steps #new position in steps #SOL position
                print("stepcount is:", self.stepcount)  
                print("time needed", self.time_needed)
            else:
                print("WARNING: velocity is 0 or None")
            return
       
      
    def get_position(self):
        return self.position  #this value is adjusted by the other functions
   
    def set_speed(self,speed):
        self.Set(self.pv_speed_set, speed)
    

    def get_speed(self):
        speed = self.Get(self.pv_speed_get)
        return speed
   
    def endstop_status(self):
        
        endstopvalue = self.Get(self.pv_endstopstatus)
        
        if endstopvalue == 0xD:
            print("upper end reached")
            return "upper"
        if endstopvalue == 0xA: #not sure!!!
            print("lower end reached")
            return "lower"
        else:
            print("no endstop reached")
            return None
        
        
    def calibration(self):
        if self.Get(self.pv_speed_get) == None:
             print("vel none")
             return

        self.pv_COM_status.put(0)
        
        self.iscalibrating = True
        self.ismoving = True
        self.direction = "neg"
      
        status = self.Get(self.pv_motor_status)
       
        while  status != 0x9 and status != 0xD: #self.Get(self.pv_motor_status) != 0xD and self.Get(self.pv_motor_status) != 0x9 : #didn't reach endstop ye
             time.sleep(0.01)
             status = self.Get(self.pv_motor_status)
             
        self.iscalibrating = False
        print("done calibrating")
        self.position = 0
        self.stepcount = 0
        self.ismoving = False
  

    def move_device_position(self):  
        """for positon plot to track the movement"""
        while True and self.is_running:
            if self.ismoving:
                velocity = self.Get(self.pv_speed_get)
                if velocity != None:
                    looptime = 0.02 #small to make sure it does not overshoot...
                    if self.direction == "pos":
                        self.position +=  velocity*looptime
                    if self.direction == "neg":
                        self.position -= velocity*looptime
                    if self.direction == "none":
                        pass
                #print(self.position)
                    print("i was avctive")
            if not self.ismoving:   
                self.position = self.stepcount
            time.sleep(0.02)  # Adjust the sleep time as needed

        self.ismoving = False
        
    def lock_for_time(self):
        """for position plot to track the movement time"""
        while True and self.is_running:
            status = self.Get(self.pv_motor_status)
            if self.time_needed > 0 and status != 0x9 and status != 0x8 and status != 0xA and status != 0x1 and status != 0x0:  #only when it has been set true in another place!!!
                #start = time.time()
                print("start counting")
                if self.direction == "pos":
                    while self.position <= self.stepcount:#time.time() - start < self.time_needed :
                        pass
                if self.direction == "neg":
                    while self.position >= self.stepcount:#time.time() - start < self.time_needed :
                        pass
                if self.iscalibrating:
                    self.direction == "neg"
                    while self.position != 0:
                        pass
                #status = self.Get(self.pv_motor_status)
                #while status == 0x9 or status == 0x8 or status == 0xA or status == 0x1 or status == 0x0: #wait till it actually stopped
                 #   pass
               
                print("ended, reset ismoving and time_needed")
                self.ismoving = False
                self.time_needed = 0 
                
        
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


class Measurement():
    """is the measurement device for all LogIV cards."""
    
    def __init__(self, server): 
        """setup all the process variables that will be needed"""
        self.full_data = [] #this grows during a measurement
        
        #waveform of the data
        self.pv_IA_wave = PV('T-MWE2IA:PROF:1')#PV('MWE2IA:PROF:1') #similar to this at least, each one possible to read 32 channels 
        self.pv_IB_wave = PV('T-MWE2IA:PROF:1') #!!!!!!!!!!!!!!!!!!! MUST CHANGE THOSE TO THE RIGHT PV'S ONCE THE FULL SETUP IS THERE!!!!!!!!!!!!!!!!!
        self.pv_IC_wave = PV('T-MWE2IA:PROF:1')
        self.pv_ID_wave = PV('T-MWE2IA:PROF:1')
        self.pv_IE_wave = PV('T-MWE2IA:PROF:1')
        
        
    def get_signal(self,motor3,goinsteps,meas_freq,point_z,point_x,point_y,endpoint_z):
        """returns a dummy signal for a certain amount of time
    
        -if signal drops below a certain value the scan must be paused
        -all 32 channels can be readout at the same time so continuous movement is OK, actually there are 160 channels, 32 per card.
        -at every point the values are stored in a frequency below 5kHz"""
        
        allchannels_onepoint = [] #will have the shape [[[32 values], position],
        # allchannels_onepoint_IB = []                                           #  [[32 values], position],    
        # allchannels_onepoint_IC = []                                              # [[32 values], position] ] AND SO ON
        # allchannels_onepoint_ID = []
        # allchannels_onepoint_IE = []
        
        
        if goinsteps == False:
            status3 = motor3.Get(motor3.pv_motor_status)
            point_z = motor3.Get(motor3.pv_SOLRB)
            
            # while point_z < motor3.Get(motor3.pv_ramp_set): #wait till the motor moves at constant speed i.e. no ramp
            #     pass
            
            while point_z != endpoint_z and status3 != 0xA and scan.scanstop == False:
                point_z = motor3.Get(motor3.pv_SOLRB)
                #print("stuck here")
                status3 = motor3.Get(motor3.pv_motor_status)
                waveform_IA = np.array(self.pv_IA_wave.get()) #is a list of 32 values
                waveform_IB = np.array(self.pv_IB_wave.get())*10
                waveform_IC = np.array(self.pv_IC_wave.get())*4
                waveform_ID = np.array(self.pv_ID_wave.get())*3
                waveform_IE = np.array(self.pv_IE_wave.get())*2 #just multiply it by some random value to get different values...
                
                #they are all in the same side by side so i can actually merge them together as there are actually 160 channels!!!! the picture is misleading!!
                full_waveform_temp = np.concatenate((waveform_IA ,waveform_IB ,waveform_IC ))
                full_waveform = np.concatenate((full_waveform_temp , waveform_ID , waveform_IE))
                
            
                current_position = [point_x,point_y,point_z] ##positons of the motors in steps... 
                
                #convert those to positions in mm
                current_position_mm = [scan.steps_to_mm(point_x,"1X"),scan.steps_to_mm(point_y,"1Y"),scan.steps_to_mm(point_z,"2Y")]
                
                allchannels_onepoint.append([full_waveform,current_position_mm])
                # allchannels_onepoint_IA.append([waveform_IA,current_position])
                # allchannels_onepoint_IB.append([waveform_IB,current_position])
                # allchannels_onepoint_IC.append([waveform_IC,current_position])
                # allchannels_onepoint_ID.append([waveform_ID,current_position])
                # allchannels_onepoint_IE.append([waveform_IE,current_position])
                
                time.sleep(1/meas_freq)  # measurement frequency
                
        if goinsteps:
            current_position = [point_x,point_y,point_z] #positons of the motors in steps...
            current_position_mm = [scan.steps_to_mm(point_x,"1X"),scan.steps_to_mm(point_y,"1Y"),scan.steps_to_mm(point_z,"2Y")]
            
            for i in range(0,meas_freq): #measure frequency time for exactly one second , repeat this 
                    
                    #this needs to be done with all 5 cards!!! 
                    waveform_IA = self.pv_IA_wave.get() #is a list of 32 values, takes one second
                    waveform_IB = self.pv_IB_wave.get()
                    waveform_IC = self.pv_IC_wave.get()
                    waveform_ID = self.pv_ID_wave.get()
                    waveform_IE = self.pv_IE_wave.get()
                    #they are all in the same side by side so i can actually merge them together as there are actually 160 channels!!!! the picture is misleading!!
                    full_waveform = waveform_IA + waveform_IB +waveform_IC + waveform_ID + waveform_IE
                    
                    # allchannels_onepoint_IA.append([waveform_IA,current_position])  #appends an array of shape [[32 values], position], meas_freq of times at each position.
                    # allchannels_onepoint_IB.append([waveform_IB,current_position])
                    # allchannels_onepoint_IC.append([waveform_IC,current_position])
                    # allchannels_onepoint_ID.append([waveform_ID,current_position])
                    # allchannels_onepoint_IE.append([waveform_IE,current_position])
                    allchannels_onepoint.append([full_waveform,current_position_mm])
                    
                    time.sleep(1/meas_freq)
        
        
        self.full_data.append(allchannels_onepoint)
    
        
    
    
    def handle_and_save_data(self,path):
        """saves the full_data array into a file and handles the format
        
        self.full_data.shape == (#positions,#measurements,[[32 values],[posx,posy,posz]])
        
        """
        if self.full_data != []:
            larger_nested_array = self.full_data
            # Save the larger nested array to a .npy file
            if path != "":
                file_path = path #+ 'scan_array'+ str(datetime.datetime.now())+'.npy'
            else:
                file_path = 'scan_array'+ str(datetime.datetime.now())+'.npy' #saves it to the same place where the program is saved
            np.save(file_path, larger_nested_array)

        #Calculate_emittance.load_array_start_calculation(file_path)
        
        # # Load the array back
        # loaded_nested_array = np.load(file_path)

        # # Print the shape of the loaded array
        # print("Shape of the loaded array:", loaded_nested_array.shape)

        
        
if __name__ == "__main__": #is only excecuted if the program is started by itself and not if called by others, here for testing...
    #try:
        # Initialize the server
        server = MotorServer()
        
        #command_queue = queue.Queue() #create the command queue through which i will issue my motor commands, in the end i will have a queue for each motor
        #command_queue2 = queue.Queue()
        command_queue3 = queue.Queue()
        
        goinsteps = True
        meas_freq = 10
        point_z= 3333
        point_x = 11
        point_y = 222
        #motor1 = server.create_and_start_motor_client(server, 1, command_queue)
        
        #motor2 = server.create_and_start_motor_client(server, 2, command_queue2)
        
        #motor3 = server.create_and_start_motor_client(server, 3, command_queue3)
        
        #num_points = 6  # Number of measurement points
        x_length = 21000  # Length of the x-axis
        y_length = 104000
        z_length = 9000
        meshsize_x = 5000
        meshsize_y = 20000
        meshsize_z = 40
    
    
        measurement = Measurement(server)
        
        #measurement.get_signal(1, goinsteps, meas_freq, point_z,point_x,point_y)
       # measurement.get_signal(1, goinsteps, meas_freq, point_z+10,point_x+177,point_y+133)
        
       
        for i in range(0,10000):
            print(measurement.pv_IA_wave.get()[1])
            time.sleep(0.001)
    
        #scan.start_scan(motor1,motor2,motor3,meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,server)    
       
        
     
        
        # server.issue_motor_command(motor1, ("calibrate",))
        # server.issue_motor_command(motor2, ("calibrate",))
        # #time.sleep(5)
        # server.issue_motor_command(motor3, ("calibrate",))
        
        # for i in range(0,2):
      
        
    
            
            # server.issue_motor_command(motor1, ("go_to_position",500))
            # #time.sleep(0.1)
            # server.issue_motor_command(motor2, ("go_to_position",500))
            # #time.sleep(0.1)
            # server.issue_motor_command(motor3, ("go_to_position",500))
                  
            # server.issue_motor_command(motor3, ("go_to_position",200))
            # server.issue_motor_command(motor1, ("go_to_position",200))
            # # time.sleep(0.1)
            # server.issue_motor_command(motor2, ("go_to_position",200))
       
    #     status1 = motor1.pv_motor_status.get()
    #     status2 = motor2.pv_motor_status.get()
    #     status3 = motor3.pv_motor_status.get()
    #     #print(status3)
    #     # motor1.stop_motor()
    #     # motor2.stop_motor()
    #     # motor3.stop_motor()
    #     print(status1,status2,status3)
    #     if status1 == 0x8 or status1 == 0x9 or status1 == 0xA and status2 == 0x8 or status2 == 0x9 or status2 == 0xA and status3 == 0x8 or status3 == 0x9 or status3 == 0xA:
    #         motor1.stop_motor()
    #         motor2.stop_motor()
    #         motor3.stop_motor()
    #         #stop server after series of commands, listening thread keeps running otherwise
       
    # #except KeyboardInterrupt:
    #     #erver.stop_server()
    #     #print("KeyboardInterrupt, the server has stopped")