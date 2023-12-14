# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 11:45:18 2023

@author: silas
"""


from epics import PV
import threading
import queue 
import time
import Measurement_script



class MotorServer:
    def __init__(self):
       self.running = True
       self.pv_status = PV('MTEST-WA81-VME02:ES:SBNT')
       self.issending = False
       
     
    def stop_server(self): #make sure that when running it again the port is accessible
        self.running = False
        
        
    def create_and_start_motor_client(self,server, MOTOR_NUMBER, command_queue,message_queue):
        motor = MotorClient(server, MOTOR_NUMBER, command_queue,message_queue) #pass the general port lock to each motor thread
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
    def __init__(self, server, MOTOR_NUMBER, command_queue, message_queue):  
        
        self.MOTOR_NUMBER = MOTOR_NUMBER
        self.initializing = True 
        self.is_running = True
        self.command_queue = command_queue
        self.message_queue = message_queue
        
        #list might be adjusted if necessary
        self.command_functions = { 
            "start": self.start_motor,
            "stop": self.stop_motor,
            "set_brake": self.set_brake,
            "set_speed": self.set_speed,
            "get_speed": self.get_speed,
            "release_brake": self.release_brake,
            "go_to_position": self.goto_position,
            "get_position": self.get_position,
            "right_endstop": self.endstop_status,
            "calibrate": self.calibration,
        }
        
        
        self.stop_flag = threading.Event()
        self.server = server
        self.MOTOR_NUMBER = MOTOR_NUMBER
       
        #set initial position
        self.position = 0  #should be at zero and then i keep track of the position by using a stepcounter!
        self.stepcount = 0
        self.time_needed = 0
        self.iscalibrating = False
  

        
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
                self.pv_targetposition_steps.put(0)
             
                
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
                self.pv_targetposition_steps.put(0)
            

                self.pv_targetposition_DRVL.put(0)
                self.pv_targetposition_DRVH.put(104172)
                self.pv_targetposition_LOPR.put(0)
                self.pv_targetposition_HOPR.put(104172)
                
            
        if MOTOR_NUMBER == 3: #correct PV's
            #initialize the pv's i am using here 
                
                self.pv_command_status = PV('T-MWE2Y:CMDE:1')
                self.pv_CHS_SBNT = PV('T-MWE2Y:CHS:1:SBNT')
                self.pv_CMD_status = PV('T-MWE2Y:CMDS:1:SBNT') #command status
                self.pv_motor_status = PV('T-MWE2Y:CHS:1')
                self.pv_brake = PV('T-MWE2Y:CMD2-BRAKE:2') #has a break
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
                self.pv_targetposition_steps.put(0)
                
                self.pv_targetposition_DRVL.put(0)
                self.pv_targetposition_DRVH.put(9600)
                self.pv_targetposition_LOPR.put(0)
                self.pv_targetposition_HOPR.put(9600)
                
                #self.calibration()
                
                time.sleep(0.5)
        if self.iscalibrating == False:
            self.initializing = False
            
        #keep track of movement for position
        self.ismoving = False
        self.direction = "pos" #default direction forward
        self.start_position_thread()
        self.start_timer_thread()

       
    def start_motor(self):
        self.is_running = True
        
    
    def stop_motor(self):
        self.stop_flag.set()
        self.is_running = False
        self.stop_position_thread()
        self.message_queue.put(">> stop")
       
    def ex_command(self,command):
        """excecutes the commands which are sent by addressing the commands from the command list which then calls the functions to execute the commands"""
        command_name, *args = command
        if command_name in self.command_functions:
                func = self.command_functions[command_name]
                func(*args)
        return "done"
    
    def run(self):  
        """
        This method runs continuously as soon as the thread is started, checking for commands in the command queue.
        Commands in the command queue are issued from the server.
        """
        print(f"Motor is running on thread {threading.current_thread().name}")
        while self.is_running and not self.stop_flag.is_set():
                if not self.server.running:
                    break
                try:
                    status = self.pv_motor_status.get()
                    if status in [0x9, 0x8, 0xA, 0x1, 0x0] and self.Get(self.server.pv_status) != 1:#much neater way of doing it!!!
                        command, result_queue = self.command_queue.get_nowait() 
                     
                        if command[0] == "get_speed":
                                speed = self.get_speed()
                                result_queue.put(speed)
                                res = "done"
                        else:
                            res = self.ex_command(command)
                            res = "done"
            
                        if res == "done":
                            self.server.issending = False
                    else: pass

                except queue.Empty:
                        if self.command_queue.empty():
                            pass
                        else:
                            self.message_queue.put(">> closed the application")
                except Exception as e:
                    self.message_queue.put(">> An unexpected error occurred: {e}")
                    
            
        
    def Set(self,pv,value):
        """sets the value of a passed process variable"""
        pv.put(value)
    

    def Get(self,pv):
        """gets the value of a passed process variable"""
        value = pv.get()
        return value
       

    def release_brake(self):
        self.Set(self.pv_brake,1) #or 0
   
    def set_brake(self):
        self.Set(self.pv_brake,0) #or 1


    def goto_position(self,position_steps):
            """moves the motor to the desired position specified by position_steps
            determines the direction of movement and checks if the velocity is 0"""
            if position_steps > self.stepcount:
                self.direction = "pos"
            if position_steps < self.stepcount: 
                self.direction = "neg"
            if position_steps == self.stepcount:
                self.direction = "none"
            
            
            velocity = self.pv_speed_get.get() 
            
            self.message_queue.put(">> velocity "+ str(velocity))
            
            if velocity !=0 and velocity!= None:
                self.Set(self.pv_targetposition_steps, position_steps) 
                self.ismoving = True 
                self.time_needed = abs(self.stepcount - int(position_steps))/velocity  
                
        
                self.stepcount = position_steps #new position in steps #SOL position
                self.message_queue.put(">> stepcount of Motor " + str(self.MOTOR_NUMBER) +" is: " + str(self.stepcount))
            else:
                self.message_queue.put(">> WARNING: velocity is 0 or None")
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
            self.message_queue.put(">> upper endstop reached")
            return "upper"
        if endstopvalue == 0xA: 
            self.message_queue.put(">> lower endstop reached")
            return "lower"
        else:
            self.message_queue.put(">> no endstop reached")
            return None
        
        
    def calibration(self):
        if self.Get(self.pv_speed_get) == None:
             self.message_queue.put(">> velocity is None")
             return

        self.pv_COM_status.put(0)
        
        self.iscalibrating = True
        self.ismoving = True
        self.direction = "neg"
      
        status = self.Get(self.pv_motor_status)
       
        while  status != 0x9 and status != 0xD: 
             time.sleep(0.01)
             status = self.Get(self.pv_motor_status)
             
        self.iscalibrating = False
        self.message_queue.put(">> done calibrating")
        self.position = 0
        self.stepcount = 0
        self.ismoving = False
  

    def move_device_position(self):  
        """for positon plot to track the movement"""
        while self.is_running:
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
            
            if not self.ismoving:   
                self.position = self.stepcount
            time.sleep(0.02) 

        self.ismoving = False
        
    def lock_for_time(self):
        """for position plot to track the movement time"""
        while self.is_running:
            status = self.Get(self.pv_motor_status)
            if self.time_needed > 0 and status != 0x9 and status != 0x8 and status != 0xA and status != 0x1 and status != 0x0:  
                if self.direction == "pos":
                    while self.position <= self.stepcount:
                        pass
                if self.direction == "neg":
                    while self.position >= self.stepcount:
                        pass
                if self.iscalibrating:
                    self.direction == "neg"
                    while self.position != 0:
                        pass
                self.ismoving = False
                self.time_needed = 0 
                
        
    def start_position_thread(self):
        self.position_thread = threading.Thread(target=self.move_device_position)
        self.position_thread.daemon = True  
        self.position_thread.start()

    def stop_position_thread(self):
        self.ismoving = False
        self.position_thread.join()

    def start_timer_thread(self):
        self.timer_thread = threading.Thread(target=self.lock_for_time)
        self.timer_thread.daemon = True  
        self.timer_thread.start()
        
    def stop_timer_thread(self):
        self.timer_thread.join()


        
if __name__ == "__main__": #is only excecuted if the program is started by itself and not if called by others, here for testing...
    
    
        #scan.start_scan(motor1,motor2,motor3,meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,server)    
       