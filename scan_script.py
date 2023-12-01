# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:41:41 2023

@author: strebe_s
"""

"""scanscript which is started from the GUI and uses commands from the communications script with the instances initialized in the GUI when the application itself starts"""

import EPICS_specific_communication as control
import matplotlib.pyplot as plt
import time
from random import random
import numpy as np
import datetime


pause_flag = False
scanstop = False

def distribute_measurement_points(num_points, x_length, y_length):
    """old function, not in use anymore...  use snake_grid instead"""

    if num_points <= 0:
        return []
    points_distribution = []
    for i in range(num_points):
        # Calculate the position of the measurement point
        x = (i % int(num_points**0.5)) * (x_length / int(num_points**0.5))
        y = (i // int(num_points**0.5)) * (y_length / int(num_points**0.5))
        points_distribution.append((x, y))
    
    # Reorder the points
    new_points_distribution = []
    for i in range(0, len(points_distribution), 2):
        new_points_distribution.append(points_distribution[i])
    for i in range(1, len(points_distribution), 2):
        new_points_distribution.append(points_distribution[i])
    new_points_distribution = new_points_distribution[::-1]
    
    # Print the reordered points
    print(new_points_distribution)
    
    return new_points_distribution


def snake_grid(num_points, x_length,y_length):
    """takes grid dimensions and number of points and return an array of tuple points arranged in a snake-like manner"""
    
    # Calculate the number of rows and columns required to fit all the points
    num_rows = int(np.ceil(np.sqrt(num_points)))
    num_cols = int(np.ceil(num_points / num_rows))

    # Create a grid of equally spaced points
    x = np.linspace(0, x_length, num_cols)
    y = np.linspace(0, y_length, num_rows)
    xx, yy = np.meshgrid(x, y)

    # Reshape the grid into a 1D array
    xx = xx.flatten() 
    yy = yy.flatten() #value remains the same for sqrt(num_points) then increases by one
    
    #change the xx values
    
    #get sequence length of xx:
    n = 0
    while(xx[n]<xx[n+1]):
        n+=1
    n += 1
    # Split the array into sequences of length n
    seqs = [xx[i:i+n] for i in range(0, len(xx), n)]

    # Reverse every other sequence
    for i in range(1, len(seqs), 2):
        seqs[i] = seqs[i][::-1]

    # Flatten the sequences and return the result
    xx = np.concatenate(seqs)
    
    # Sort the points in a snake-like pattern
    grid_points = np.column_stack((xx, yy))
    print(grid_points)
    
    # Return the points as a 2D array
    return grid_points


def plot_measurement_points(points_distribution, x_length, y_length):
    """creates a 2D plot of the measurement points on the grid"""
    # Create a scatter plot of the measurement points
    plt.scatter(*zip(*points_distribution), marker='o', color='blue', label='Measurement Points')
    
    # Set the x and y axis limits based on the provided lengths
    plt.xlim(0, x_length)
    plt.ylim(0, y_length)
    
    # Add labels and legend
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Measurement Points on 2D Grid')
    plt.legend()
    
    # Display the plot
    plt.grid(True)
    plt.show()


# def wait_for_server(server):
#     """i can do this with a 'status' variable"""
#     while server.issending == True:
#         pass
#     return "done"


def calculate_mesh_points_2d(mesh_size_x, mesh_size_y, overall_dimension_x, overall_dimension_y):
    """
    Calculate the number of mesh points in each dimension for a 2D mesh.

    Parameters:
    - mesh_size_x (float): The size of the mesh in the x-dimension.
    - mesh_size_y (float): The size of the mesh in the y-dimension.
    - overall_dimension_x (float): The overall dimension of the mesh in the x-dimension.
    - overall_dimension_y (float): The overall dimension of the mesh in the y-dimension.

    Returns:
    - int: The total number of mesh points in the 2D mesh.
    """
    # Calculate the number of mesh points in each dimension
    num_points_x = int((overall_dimension_x / mesh_size_x) + 1)
    num_points_y = int((overall_dimension_y / mesh_size_y) + 1)
    
    # Calculate the total number of mesh points
    total_points = num_points_x * num_points_y
    
    return total_points


def start_scan(directory,saveit,meas_freq,goinsteps,message_queue,motor1,motor2,motor3,meshsize_x,meshsize_y,meshsize_z,x1_setup_val,y1_setup_val,y2_setup_val,server): #this will then issue the commands through the right command queue
    """should start a scan preferably in an independent thread
    
    -..._setup_val = (..min,..max,..speed) #use the max/min in an advanced version later... for now always go to the end...
    """
    global pause_flag, scanstop
    
    scanstop = False
    
    measurement = control.Measurement(server) #start meas device for one card (or several later)
    
    
   
    
    x_speed = x1_setup_val[2]
    y_speed = y1_setup_val[2]
    z_speed = y2_setup_val[2]
    
    x_length = x1_setup_val[1] - x1_setup_val[0]
    y_length = y1_setup_val[1] - y1_setup_val[0]
    z_length = y2_setup_val[1] - y2_setup_val[0]
    
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
    
    number_of_points = calculate_mesh_points_2d(meshsize_x, meshsize_y, x_length,y_length)
    message_queue.put("number of points: " + str(number_of_points))
    
    estimated_time = time_estimation(meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,x_speed, y_speed, z_speed, number_of_points)
    
    message_queue.put(">> the scan will take approx. " + str(estimated_time) + " min")
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes = estimated_time)
    #show_scan_time(start_time,end_time)
    message_queue.put((start_time,end_time))
    #print("the scan will take approx.", estimated_time, "min")
    answer = "y" #input("do you want to proceed? (y/n")
    if answer == "y":
        
        #start with recalibration of the motors:
        server.issue_motor_command(motor1,("calibrate",),isreturn = 0)
       
        server.issue_motor_command(motor2,("calibrate",),isreturn = 0)
       
        server.issue_motor_command(motor3,("calibrate",),isreturn = 0)
      
        
        while motor1.iscalibrating == True or motor2.iscalibrating == True or motor3.iscalibrating == True: #wait for calibration to be done
            time.sleep(0.1)
            print("is calibrating")
 
     
        server.issue_motor_command(motor1,("set_speed",x_speed),isreturn = 0)
        server.issue_motor_command(motor2,("set_speed",y_speed),isreturn = 0)
        server.issue_motor_command(motor3,("set_speed",z_speed),isreturn = 0)
        
        
        
        
        
        point_distribution = snake_grid(number_of_points,x_length,y_length)
        print(point_distribution)
        
        endposition_x = point_distribution[-1][0]
        endposition_y = point_distribution[-1][1]
        endposition_z = z_length
        start_position_z = 0
        
    
        for i in range(len(point_distribution)):
            if scanstop:
                 message_queue.put(">> scan stopped")
                 break
            if server.running == True:  #check that QtApplication has not been closed
                point_x = point_distribution[i][0]
                point_y = point_distribution[i][1]
                
                
                print(point_x,point_y)
                

                moving = False
                while moving == False: #wait till motors are free and stopped
                    if server.running == False:
                        print("server closed")
                        return
                    if scanstop:
                        message_queue.put(">> scan stopped")
                        break  
                    while pause_flag:
                        print("Pausing...")
                        time.sleep(0.5)  # Adjust the sleep time based on your requirements
                        message_queue.put("Pausing...")
                    
                    status1 = motor1.Get(motor1.pv_motor_status)
                    status2 = motor2.Get(motor2.pv_motor_status)
                    status3 = motor3.Get(motor3.pv_motor_status)
                    if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
                      if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
                          z_pos = motor3.Get(motor3.pv_SOLRB) #only one read necessary
                          goingup = z_pos <= 9600 and z_pos >= 1000 #enable parallel movement to reduce time cost!
                          if status3 == 0x9 or z_pos == endposition_z or goingup  and motor3.Get(server.pv_status) != 1 :  #not moving and at upper endpoint
                        
                            server.issue_motor_command(motor1,("go_to_position",point_x))  #moves motor on thread one
                           
                            server.issue_motor_command(motor2,("go_to_position",point_y)) #moves motor on thread two
                           
                            moving = True
                            print("starts to move")
                          else: time.sleep(0.1)
                      else: time.sleep(0.1)
                    else: time.sleep(0.1)
                          
    
                status2 = motor2.Get(motor2.pv_motor_status)
                while status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0: #wait till it actually started moving
                    time.sleep(0.05)
                    status2 = motor2.Get(motor2.pv_motor_status)
                
                while moving == True: #wait until motors are done moving
                    status1 = motor1.Get(motor1.pv_motor_status)
                    status2 = motor2.Get(motor2.pv_motor_status)
                    if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : 
                      if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1  : 
                    #if motor1.ismoving == True or motor2.ismoving == True:  #check that motors are actually free to move
                        moving = False 
                        print("arrived at point")
                      
                      else: pass
                    else: pass
                      
               
                # while motor1.Get(motor1.pv_SOLRB) != point_x and motor2.Get(motor2.pv_SOLRB) != point_y and scanstop == False:
                #     time.sleep(0.1)
                #     if point_x == endposition_x and point_y == endposition_y:
                #         break
                        
                #     print("waiting to set position")
                
                if scanstop:
                    message_queue.put(">> scan stopped")
                    break
                
                start_readout(meas_freq,goinsteps,message_queue,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server,measurement,point_x,point_y)
            
              
                print("go again")
            else:
                print("ERROR: GUI/server has been closed")
                return 
                
        
        # while motor1.Get(motor1.pv_SOLRB) != endposition_x and motor2.Get(motor2.pv_SOLRB) != endposition_y:
        #     pass
        print("scan is done")
        
        #return 
    else:
        print("abort scan script")
        return 
    scanstop = False
    
    
    if saveit == True:
        print("wanna handle data")
        measurement.handle_and_save_data(directory)
    
    return 

def start_readout(meas_freq,goinsteps,message_queue,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server,measurement,point_x, point_y):
    """does readout stuff"""
    print("start readout")
    
    
    
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
               print("Pausing...")
               time.sleep(0.5)  # Adjust the sleep time based on your requirements
               message_queue.put(">>Pauseing...")
            if scanstop:
                 message_queue.put(">> scan stopped")
                 break 
             
                
        
            status1 = motor1.Get(motor1.pv_motor_status)
            status2 = motor2.Get(motor2.pv_motor_status)
            status3 = motor3.Get(motor3.pv_motor_status)
            if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
              if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
                  if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  and motor3.Get(motor3.pv_SOLRB) == start_point:
            
                    server.issue_motor_command(motor3,("go_to_position",endpoint_z))
                    moving = True
                    
                  else: pass 
              else: pass 
            else: pass 
       
        status3 = motor3.Get(motor3.pv_motor_status)
        while status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0: #wait till it actually started moving
            status3 = motor3.Get(motor3.pv_motor_status)
        
        current_position = 0 #whaterver
        measurement.get_signal(motor3,goinsteps,meas_freq,current_position,point_x,point_y,endpoint_z) #start collecting data
        
        while moving == True: #wait until motors are done moving
            status3 = motor3.Get(motor3.pv_motor_status)
            if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
                moving = False 
            else: pass
               
     # Check the pause flag
        while pause_flag:
            print("Pausing...")
            message_queue.put(">>Pauseing...")
            time.sleep(1)  # Adjust the sleep time based on your requirements
        
      
        
        server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   

    if goinsteps == True:
        steps = int((z_length-start_point)/meshsize_z) #rounded down number of steps to take to next int
        
        current_position = start_point
        
        #safety check if collimator is not moving
        allgood = False
        while allgood == False:
            status1 = motor1.Get(motor1.pv_motor_status)
            status2 = motor2.Get(motor2.pv_motor_status)
            if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
                    if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
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
                   print("Pausing...")
                   time.sleep(0.5)  # Adjust the sleep time based on your requirements
                   message_queue.put(">>Pauseing...")
                if scanstop:
                     message_queue.put(">> scan stopped")
                     break 
                
            
                #status3 = motor3.Get(motor3.pv_motor_status)
                command3stat = motor3.Get(motor3.pv_command_status)
                print(command3stat)
                #if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1: #  and motor3.Get(motor3.pv_SOLRB) == start_point:
                if command3stat == 0x100 or command3stat == 0x0 :
                        server.issue_motor_command(motor3,("go_to_position",current_position))
                        print("now")
                        moving = True
                else: pass 
   
            status3 = motor3.Get(motor3.pv_motor_status)
            while status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0: #wait till it actually started moving
                status3 = motor3.Get(motor3.pv_motor_status)
            
            while moving == True: #wait until motors are done moving
                command3stat = motor3.Get(motor3.pv_command_status)
                status3 = motor3.Get(motor3.pv_motor_status)                           
                      #maybe this one is good enough to make it go faster?
                if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
                #if command3stat == 0x100 or command3stat == 0x0:
                    moving = False 
     
                    measurement.get_signal(motor3,goinsteps,meas_freq,current_position,point_x,point_y,endpoint_z)
                else: pass
         # Check the pause flag
        while pause_flag:
            print("Pausing...")
            message_queue.put(">>Pauseing...")
            time.sleep(1)  # Adjust the sleep time based on your requirements
        
        #server.issue_motor_command(motor3,("go_to_position",end_point))
        server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   

    return 
    

        
"""   
def get_signal(motor3,goinsteps,meas_freq,current_position):
    #returns a dummy signal for a certain amount of time
    
    #-if signal drops below a certain value the scan must be paused
    #-all 32 channels can be readout at the same time so continuous movement is OK, actually there are 160 channels, 32 per card.
    #-at every point the values are stored in a frequency below 5kHz
    allchannels_onepoint = np.zeros((32,meas_freq)) #10 points for all 32 channels
    data = []
    status3 = motor3.Get(motor3.pv_motor_status)
    if goinsteps == False:
        while status3 != 0xA:
            status3 = motor3.Get(motor3.pv_motor_status)
            data.append(np.random.randint(1000)) #this would correspond to a 
            time.sleep(0.1)  #10Hz measurement frequency
            
    else:
        #for j in range(0,32): #fill the array
        for i in range(0,meas_freq): #measure frequency time for exactly one second 
                allchannels_onepoint[1][i] = np.random.randint(1000) #only put data in one channel for now...
                time.sleep(1/meas_freq)
    full_data.append([allchannels_onepoint,current_position])
    #print(full_data)
"""  
   
def time_estimation(mesh_size_x,mesh_size_y,mesh_size_z,x_length,y_length,z_length,x_speed, y_speed, z_speed,number_of_points):
   
    """
    Estimate the time for a scan through a mesh of points. Sum the time it takes to go through all the points if there was no parallel movement, though not taking into account the processing time
     
    Parameters:
    - mesh_size_x (float): The size of the mesh in the x-dimension.
    - mesh_size_y (float): The size of the mesh in the y-dimension.
    - mesh_size_z (float): The size of the mesh in the z-dimension.
    - x_length (float): The overall length of the scan in the x-dimension.
    - y_length (float): The overall length of the scan in the y-dimension.
    - z_length (float): The overall length of the scan in the z-dimension.
    - x_speed (float): The speed of the scan in the x-dimension.
    - y_speed (float): The speed of the scan in the y-dimension.
    - z_speed (float): The speed of the scan in the z-dimension.
     
    Returns:
    - float: The estimated time for the scan.
    """
    # Calculate the total distance in each dimension
    total_distance_x = x_length + (mesh_size_x - x_length % mesh_size_x)  # Ensure it covers the last row
    total_distance_y = y_length + (mesh_size_y - y_length % mesh_size_y)  # Ensure it covers the last column
   
    total_distance_z = number_of_points*(2*z_length + (mesh_size_z - z_length % mesh_size_z))  # Ensure it covers the last depth

    # Calculate the time for the scan in each dimension
    time_x = total_distance_x / x_speed
    time_y = total_distance_y / y_speed
    time_z = total_distance_z / z_speed
 
    # estimate of processing time...
    proc = max(x_length,y_length,z_length)/min(mesh_size_x,mesh_size_y,mesh_size_z)
    proc_time = proc*2
    
    total_time = time_x + time_y + time_z + proc_time #in seconds
    minutes = round(total_time/60,2)
    # Return the maximum time as it determines the overall scan time
    return minutes


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
    global scanstop
    scanstop = True
    
    
    
def steps_to_mm(steps,axis,isspeed=False): 
    """converts steps to mm for the particular axis i.e. string "1X","1Y" and "2Y" """
    """adjust this function s.t. 0mm means on axis"""
    
    if axis == "1X":
        mm = steps/535 #mm away from CCW
        mapped_mm = (1/535)*steps - 20.5
    elif axis == "1Y":
        mm = steps/800
        mapped_mm = (1/800)*steps - 125
    elif axis == "2Y":
        mm = steps/50
        mapped_mm = (1/50)*steps - 150
    else: print("ERROR, NO VALID AXIS")
    if isspeed:
        return mm
    else:
        return mapped_mm
        
def mm_to_steps(mm,axis, isspeed = False):
    """converts mm to steps for the particular axis i.e. string "1X","1Y" and "2Y" """
    """adjust this function s.t. 0mm means on axis"""
    
    
    if axis == "1X":
        steps = mm*535
        remapped_steps = 20.5*535 + mm*535
    elif axis == "1Y":
        steps = mm*800
        remapped_steps = 125*800 + mm*800
    elif axis == "2Y":
        steps = mm*50
        remapped_steps = 150*50 + mm*50
    else: print("ERROR, NO VALID AXIS")
    
    if isspeed:
        return steps
    else:    
        return remapped_steps



# # # # Example usage:
# num_points = 6  # Number of measurement points
# x_length = 21700  # Length of the x-axis
# y_length = 104000 # Length of the y-axis

#measurement_points = distribute_measurement_points(num_points, x_length, y_length)
#points_distribution = snake_grid(num_points,x_length, y_length)
# #plot_measurement_points(measurement_points, x_length, y_length)

# start_scan(1,1,num_points, x_length, y_length,1)