# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:41:41 2023

@author: strebe_s
"""

"""scanscript which is started from the GUI and uses commands from the communications script with the instances initialized in the GUI when the application itself starts"""


import matplotlib.pyplot as plt
import time
import numpy as np
import datetime
import Measurement_script 
import scan_script_service_functions as func

pause_flag = False
scanstop = False


"""
Status values:
0x9 -> brake and -lim
0xA -> brake and +lim
0x1 or 0x0 -> not calibrated
0x8 -> brake and no lim

"""

def start_scan(directory,saveit,meas_freq,goinsteps,message_queue,motor1,
               motor2,motor3,meshsize_x,meshsize_y,meshsize_z,
               x1_setup_val,y1_setup_val,y2_setup_val,server): #this will then issue the commands through the right command queue
    """should start a scan preferably in an independent thread
    
    -..._setup_val = (..min,..max,..speed) #use the max/min in an advanced version later... for now always go to the end...
    """
    global pause_flag, scanstop
    
    scanstop = False
    
    measurement = Measurement_script.Measurement(server) #start meas device for one card (or several later)
    
    
    x_speed = x1_setup_val[2]
    y_speed = y1_setup_val[2]
    z_speed = y2_setup_val[2]
    
    x_length = abs(x1_setup_val[1] - x1_setup_val[0])
    y_length = abs(y1_setup_val[1] - y1_setup_val[0])
    z_length = abs(y2_setup_val[1] - y2_setup_val[0])
    
    
    
    if meshsize_x > x_length or meshsize_y > y_length or meshsize_z > z_length:
        print(">> INVALID mesh or dimensions")
        message_queue.put(">> INVALID mesh or dimensions")
        return
    

    if x_speed == None or y_speed == None or z_speed == None:
        message_queue.put(">> speed inputs not valid, use defaults")
        x_speed = 1800
        y_speed = 1800
        z_speed = 1800
    if x_length == None  or y_length == None or z_length == None:
        message_queue.put(">> speed inputs not valid, use defaults")
        x_length = 21700
        y_length = 104000
        z_length = 9600
    
    number_of_points = func.calculate_mesh_points_2d(meshsize_x, meshsize_y, x_length,y_length)
    message_queue.put(">> number of points: " + str(number_of_points))
    
    #runtime estimation in minutes
    estimated_time = func.time_estimation(goinsteps,meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,x_speed, y_speed, z_speed, number_of_points)
    
    message_queue.put(">> the scan will take approx. " + str(estimated_time) + " min")
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes = estimated_time)
    
    #send values to display function
    message_queue.put((start_time,end_time))
 
    #start with recalibration of the motors:
    server.issue_motor_command(motor1,("calibrate",),isreturn = 0)
    server.issue_motor_command(motor2,("calibrate",),isreturn = 0)
    server.issue_motor_command(motor3,("calibrate",),isreturn = 0)
  
    
    while motor1.iscalibrating == True or motor2.iscalibrating == True or motor3.iscalibrating == True: #wait for calibration to be done
        time.sleep(0.1)
        message_queue.put(">> is calibrating")
     
 
    server.issue_motor_command(motor1,("set_speed",x_speed),isreturn = 0)
    server.issue_motor_command(motor2,("set_speed",y_speed),isreturn = 0)
    server.issue_motor_command(motor3,("set_speed",z_speed),isreturn = 0)
    
    
    point_distribution = func.snake_grid(number_of_points,x_length,y_length)
    
    #endposition_x = point_distribution[-1][0]
    #endposition_y = point_distribution[-1][1]
    endposition_z = z_length
    #start_position_z = 0
    
    for i in range(len(point_distribution)):
        if scanstop:
             message_queue.put(">> scan stopped")
             break
        if server.running == True:  #check that Application has not been closed
            point_x = point_distribution[i][0]
            point_y = point_distribution[i][1]
            
            message_queue.put(str(point_x)+ ", "+ str(point_y))
            
            moving = False
            while moving == False: #wait till motors are free and stopped
                
                if server.running == False:
                    message_queue.put(">> server closed")
                    return
                if scanstop:
                    message_queue.put(">> scan stopped")
                    break  
                while pause_flag:
                    time.sleep(0.5)  # Adjust the sleep time based on your requirements
                    message_queue.put(">> Pausing...")
                
                
                status1 = motor1.Get(motor1.pv_motor_status)
                status2 = motor2.Get(motor2.pv_motor_status)
                status3 = motor3.Get(motor3.pv_motor_status)
                if status1 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor1.Get(server.pv_status) != 1:#not moving
                  if status2 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor2.Get(server.pv_status) != 1:
                      z_pos = motor3.Get(motor3.pv_SOLRB) #only one read necessary
                      goingup = z_pos <= 9600 and z_pos >= 1000 #enable parallel movement to reduce time cost!
                      if status3 == 0x9 or z_pos == endposition_z or goingup  and motor3.Get(server.pv_status) != 1 :  #not moving and at upper endpoint
                    
                        server.issue_motor_command(motor1,("go_to_position",point_x))  #moves motor on thread one
                        server.issue_motor_command(motor2,("go_to_position",point_y)) #moves motor on thread two
                       
                        moving = True
                      else: time.sleep(0.1)
                  else: time.sleep(0.1)
                else: time.sleep(0.1)
                      

            status2 = motor2.Get(motor2.pv_motor_status)
            while status2 in [0x9, 0x8, 0xA, 0x1, 0x0]:#wait till it actually started moving
                time.sleep(0.05)
                status2 = motor2.Get(motor2.pv_motor_status)
            
            while moving == True: #wait until motors are done moving
                status1 = motor1.Get(motor1.pv_motor_status)
                status2 = motor2.Get(motor2.pv_motor_status)
                if status1 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor1.Get(server.pv_status) != 1:#not moving
                  if status2 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor2.Get(server.pv_status) != 1:
   
                    moving = False 
                    message_queue.put(">> arrrived at point")
                  else: pass
                else: pass
                  
           
            if scanstop:
                message_queue.put(">> scan stopped")
                break
            
            start_readout(meas_freq,goinsteps,message_queue,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server,measurement,point_x,point_y)
        
        else:
            print("ERROR: server has been closed")
            message_queue.put(">> ERROR: server has been closed")
            return 
            

    message_queue.put(">> scan is done")

    scanstop = False
    
    
    if saveit == True:
        message_queue.put(">> handle measured data")
        measurement.handle_and_save_data(directory)
    
    return 

def start_readout(meas_freq,goinsteps,message_queue,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server,measurement,point_x, point_y):
    """When the collimator arrived at its desired position this function is called.
    - The readout grid starts to move through the beam and measures the current.
    - When it arrives at the endpoint the grid will move back to start without measuring and at the same time the collimator readjusts to the next position
    """

    readout_speed = z_speed
    server.issue_motor_command(motor3,("set_speed",readout_speed))

    endpoint_z = z_length
    start_point = 0
    
    moving = False

    if goinsteps == False:
        while moving == False: #wait till motors are free and stopped
            if scanstop:
              message_queue.put(">> scan stopped")
              break
            if server.running == False:
                return
            
            # Check the pause flag
            while pause_flag:
               message_queue.put(">> Pausing...")
               time.sleep(1)  # Adjust the sleep time based on your requirements
            if scanstop:
                 message_queue.put(">> scan stopped")
                 break 
             
            status1 = motor1.Get(motor1.pv_motor_status)
            status2 = motor2.Get(motor2.pv_motor_status)
            status3 = motor3.Get(motor3.pv_motor_status) 
            if status1 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor1.Get(server.pv_status) != 1:#not moving
              if status2 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor2.Get(server.pv_status) != 1:
                  if status3 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor3.Get(server.pv_status) != 1 and motor3.Get(motor3.pv_SOLRB) == start_point:
            
                    server.issue_motor_command(motor3,("go_to_position",endpoint_z))
                    
                    moving = True
                    
                  else: pass 
              else: pass 
            else: pass 
       
        status3 = motor3.Get(motor3.pv_motor_status)
        while status3 in [0x9, 0x8, 0xA, 0x1, 0x0]: #wait till it actually started moving
            status3 = motor3.Get(motor3.pv_motor_status)
        
        point_z = None #whaterver, not in use in this case
        measurement.get_signal(motor3,goinsteps,meas_freq,point_z,point_x,point_y,endpoint_z) #start collecting data
        
        while moving == True: #wait until motors are done moving
            status3 = motor3.Get(motor3.pv_motor_status)
            if status3 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor3.Get(server.pv_status) != 1:
                moving = False 
            else: pass
               
     # Check the pause flag
        while pause_flag:
            message_queue.put(">> Pausing...")
            time.sleep(1)  # Adjust the sleep time based on your requirements
        
     
        server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   
    
    """---- Measure in steps -----------------------------------------------------------------------------------------------------------------------------"""
    """this part is rather slow because so far i could not manage to get the steps without the break to go on and off and not loose any commands in between...., this is therefore a safer but slow version"""
    
    if goinsteps == True:
        steps = int((z_length-start_point)/meshsize_z) #rounded down number of steps to take to next int
        
        current_position = start_point
        
        #safety check if collimator is not moving
        allgood = False
        while allgood == False:
            status1 = motor1.Get(motor1.pv_motor_status)
            status2 = motor2.Get(motor2.pv_motor_status)
            if status1 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor1.Get(server.pv_status) != 1:
                    if status2 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor2.Get(server.pv_status) != 1:
                        allgood = True
                    else: allgood = False
            else: allgood = False

        for i in range(0,steps+1):
            current_position += meshsize_z
            moving = False
            if scanstop:
                 message_queue.put(">> scan stopped")
                 break
            while moving == False: #wait till motors are free and stopped
                
                if server.running == False:
                    return
                
                # Check the pause flag
                while pause_flag:
                   time.sleep(1)  # Adjust the sleep time based on your requirements
                   message_queue.put(">> Pausing...")
                if scanstop:
                     message_queue.put(">> scan stopped")
                     break 
                
            
                
                command3stat = motor3.Get(motor3.pv_command_status)
                if command3stat in [0x100, 0x0]:
                        server.issue_motor_command(motor3,("go_to_position",current_position))
                        moving = True
                else: pass 
   
            status3 = motor3.Get(motor3.pv_motor_status)
            while status3 in [0x9,0x8,0xA,0x1,0x0]: #wait till it actually started moving
                status3 = motor3.Get(motor3.pv_motor_status)
    
            
            while moving == True: #wait until motors are done moving
                command3stat = motor3.Get(motor3.pv_command_status)
                status3 = motor3.Get(motor3.pv_motor_status)                           
                if status3 in [0x9, 0x8, 0xA, 0x1, 0x0] and motor3.Get(server.pv_status) != 1: #this prevents it to be faster, it's safe this way but takes a lot of time...
                    moving = False 
                    measurement.get_signal(motor3,goinsteps,meas_freq,current_position,point_x,point_y,endpoint_z) #make a measurement at this position
                else: pass
        
        # Check the pause flag
        while pause_flag:
            message_queue.put(">> Pausing...")
            time.sleep(1)  # Adjust the sleep time based on your requirements
        
        #server.issue_motor_command(motor3,("go_to_position",end_point))
        server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   
    return 

def pause_scan():
    """when the pause button is clicked on the GUI the scan procedure should pause and not go to the next point"""
    global pause_flag
    pause_flag = True
    return

def continue_scan():
    """continue scan after a pause"""
    global pause_flag
    pause_flag = False
    
def stop_scan():
    """sets stop flag to true; will stop be caught in the scan function.
    Then scan then stops and the data measured up until then is saved if chosen."""
    
    global scanstop
    scanstop = True

