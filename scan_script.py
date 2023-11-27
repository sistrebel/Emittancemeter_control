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


pause_flag = False
scanstop = False

full_data = []

def distribute_measurement_points(num_points, x_length, y_length):
    """old function"""

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
    
    # print(xx)
    # print(yy) #these are good 1D arrays! 
    
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
# Example usage:

def wait_for_server(server):
    """i can do this with a 'status' variable"""
    while server.issending == True:
        pass
    return "done"


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


def start_scan(show_message,motor1,motor2,motor3,meshsize_x,meshsize_y,meshsize_z,x1_setup_val,y1_setup_val,y2_setup_val,server): #this will then issue the commands through the right command queue
    """should start a scan preferably in an independent thread
    
    -..._setup_val = (..min,..max,..speed) #use the max/min in an advanced version later... for now always go to the end...
    """
    global pause_flag, scanstop
    
    
    
    x_speed = x1_setup_val[2]
    y_speed = y1_setup_val[2]
    z_speed = y2_setup_val[2]
    
    x_length = x1_setup_val[1] - x1_setup_val[0]
    y_length = y1_setup_val[1] - y1_setup_val[0]
    z_length = y2_setup_val[1] - y2_setup_val[0]
    
    if x_speed == None or y_speed == None or z_speed == None:
        x_speed = 1800
        y_speed = 1800
        z_speed = 1800
    if x_length == None  or y_length == None or z_length == None:
        x_length = 21700
        y_length = 104000
        z_length = 9000
    
    estimated_time = time_estimation(meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,x_speed, y_speed, z_speed)
    
    show_message(">> the scan will take approx." + str(estimated_time) + "min")
    
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
        
        
        number_of_points = calculate_mesh_points_2d(meshsize_x, meshsize_y, x_length,y_length)
        
        print("number of points", number_of_points)
        
        point_distribution = snake_grid(number_of_points,x_length,y_length)
        print(point_distribution)
        
        endposition_x = point_distribution[-1][0]
        endposition_y = point_distribution[-1][1]
        endposition_z = z_length
        start_position_z = 0
        
    
        for i in range(len(point_distribution)):
            if scanstop:
                 #show_message(">> scan stopped")
                 break
            if server.running == True:  #check that QtApplication has not been closed
                point_x = point_distribution[i][0]
                point_y = point_distribution[i][1]
                
                
                print(point_x,point_y)
                
                
                #estimate the time it takes to move from current position to target position here
                #time_needed = time_estimation(old_point, new_point, x_speed, y_speed)
              
                moving = False
                while moving == False: #wait till motors are free and stopped
                    if server.running == False:
                        print("server closed")
                        return
                    if scanstop:
                        show_message(">> scan stopped")
                        break 
                    while pause_flag:
                        print("Pausing...")
                        time.sleep(0.5)  # Adjust the sleep time based on your requirements
                        show_message("Pausing...")
                    
                    status1 = motor1.Get(motor1.pv_motor_status)
                    status2 = motor2.Get(motor2.pv_motor_status)
                    status3 = motor3.Get(motor3.pv_motor_status)
                    if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
                      if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
                          if status3 == 0x9 or motor3.Get(motor3.pv_SOLRB) == endposition_z  and motor3.Get(server.pv_status) != 1 :  #not moving and at upper endpoint
                            if motor3.Get(motor3.pv_SOLRB) == endposition_z:
                                time.sleep(1) #give it time
                                
                    # if motor1.ismoving == False and  motor2.ismoving == False:  #check that motors are actually free to move
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
                        #time.sleep(0.05)
                        #print("still moving")
                    else: pass
                        #time.sleep(0.1)
                        #print("still moving")
               
                while motor1.Get(motor1.pv_SOLRB) != point_x and motor2.Get(motor2.pv_SOLRB) != point_y and scanstop == False:
                    time.sleep(0.1)
                    if point_x == endposition_x and point_y == endposition_y:
                        break
                        
                    print("waiting to set position")
     
                
                data = start_readout(show_message,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server)
            
                full_data.append(data)
            
           
                print("go again")
            else:
                print("ERROR: GUI/server has been closed")
                return
                
        
        
        while motor1.Get(motor1.pv_SOLRB) != endposition_x and motor2.Get(motor2.pv_SOLRB) != endposition_y:
            pass
        print("scan is done")
        print(full_data)
        return
    else:
        print("abort scan script")
        return
    scanstop = False

def start_readout(show_message,motor1,motor2,motor3,z_length,meshsize_z,z_speed,server):
    """does readout stuff"""
    print("start readout")
    
    
    readout_speed = z_speed

    server.issue_motor_command(motor3,("set_speed",readout_speed),isreturn = 0)

    end_point = z_length
    start_point = 0
    
    moving = False

    while moving == False: #wait till motors are free and stopped
        if scanstop:
          #show_message(">> scan stopped")
          break
        if server.running == False:
            return
        
        # Check the pause flag
        while pause_flag:
           print("Pausing...")
           time.sleep(0.5)  # Adjust the sleep time based on your requirements
           show_message("Pauseing...")
        if scanstop:
             show_message(">> scan stopped")
             break 
        # status3 = motor3.Get(motor3.pv_motor_status)
        # if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :   #check that motors are actually free to move, readjusting takes time as well
        status1 = motor1.Get(motor1.pv_motor_status)
        status2 = motor2.Get(motor2.pv_motor_status)
        status3 = motor3.Get(motor3.pv_motor_status)
        if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
          if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
              if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  and motor3.Get(motor3.pv_SOLRB) == start_point:
        
                server.issue_motor_command(motor3,("go_to_position",end_point),)
                moving = True
                
              else: pass #time.sleep(0.2)
          else: pass #time.sleep(0.2)
        else: pass #time.sleep(0.2)
    #time.sleep(time_needed)
    
    #time.sleep(time_needed)
    status3 = motor3.Get(motor3.pv_motor_status)
    while status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0: #wait till it actually started moving
        #time.sleep(0.05)
        print("stuck")
        status3 = motor3.Get(motor3.pv_motor_status)
    
    get_signal(motor3) #start collecting data
    
    while moving == True: #wait until motors are done moving
        status3 = motor3.Get(motor3.pv_motor_status)
        if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
            moving = False 
            #print("arrived at point")
            #print(get_signal())
            #server.issue_motor_command(motor3,("go_to_position",start_point),isreturn = 0)
        else: print("stuck here")#pass
            #time.sleep(0.05)
             #simulate the readout while the motor is moving
 # Check the pause flag
    while pause_flag:
        print("Pausing...")
        show_message("Pauseing...")
        time.sleep(1)  # Adjust the sleep time based on your requirements
    
    #server.issue_motor_command(motor3,("go_to_position",end_point))
    #print("i am heeeeeeeeeeereeeeeeee")
    server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   
# while moving == True: #wait until motors are done moving, wait for last step and go back 
#      status3 = motor3.Get(motor3.pv_motor_status)
#      if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
#          moving = False 
#          #print("arrived at point")
#          #print(get_signal())
         
#      else:
#          time.sleep(0.05)
#           #simulate the readout while the motor is moving

    
    """
    steps = int((z_length-start_point)/meshsize_z) #rounded down number of steps to take to next int
    
    current_position = start_point
    
    #like this it is in steps but i can also make it moving continuously as rudolf said... readout of the 32 channels can be done in parallel
    
    #time_needed = time_estimation(start_point, end_point, readout_speed,readout_speed)
    for i in range(0,steps):
        current_position += meshsize_z
        moving = False
        if scanstop:
             #show_message(">> scan stopped")
             break
        while moving == False: #wait till motors are free and stopped
            
            if server.running == False:
                return
            
            # Check the pause flag
            while pause_flag:
               print("Pausing...")
               time.sleep(0.5)  # Adjust the sleep time based on your requirements
               show_message("Pauseing...")
            if scanstop:
                 show_message(">> scan stopped")
                 break 
            # status3 = motor3.Get(motor3.pv_motor_status)
            # if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :   #check that motors are actually free to move, readjusting takes time as well
            status1 = motor1.Get(motor1.pv_motor_status)
            status2 = motor2.Get(motor2.pv_motor_status)
            status3 = motor3.Get(motor3.pv_motor_status)
            if status1 == 0x9 or status1 == 0x8 or status1 == 0xA or status1 == 0x1 or status1 == 0x0 and motor1.Get(server.pv_status) != 1  : #not moving
              if status2 == 0x9 or status2 == 0x8 or status2 == 0xA or status2 == 0x1 or status2 == 0x0 and motor2.Get(server.pv_status) != 1 : #not moving
                  if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  and motor3.Get(motor3.pv_SOLRB) == start_point:
            
                    server.issue_motor_command(motor3,("go_to_position",current_position),)
                    moving = True
                    
                  else: pass #time.sleep(0.2)
              else: pass #time.sleep(0.2)
            else: pass #time.sleep(0.2)
        #time.sleep(time_needed)
        
        #time.sleep(time_needed)
        status3 = motor3.Get(motor3.pv_motor_status)
        while status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0: #wait till it actually started moving
            #time.sleep(0.05)
            status3 = motor3.Get(motor3.pv_motor_status)
        
        while moving == True: #wait until motors are done moving
            status3 = motor3.Get(motor3.pv_motor_status)
            if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
                moving = False 
                #print("arrived at point")
                #print(get_signal())
                #server.issue_motor_command(motor3,("go_to_position",start_point),isreturn = 0)
            else: pass
                #time.sleep(0.05)
                 #simulate the readout while the motor is moving
     # Check the pause flag
    while pause_flag:
        print("Pausing...")
        show_message("Pauseing...")
        time.sleep(1)  # Adjust the sleep time based on your requirements
    
    server.issue_motor_command(motor3,("go_to_position",end_point))
    print("i am heeeeeeeeeeereeeeeeee")
    server.issue_motor_command(motor3,("go_to_position",start_point)) #go back directly   
    # while moving == True: #wait until motors are done moving, wait for last step and go back 
    #      status3 = motor3.Get(motor3.pv_motor_status)
    #      if status3 == 0x9 or status3 == 0x8 or status3 == 0xA or status3 == 0x1 or status3 == 0x0 and motor3.Get(server.pv_status) != 1  :  #check that motors are actually free to move
    #          moving = False 
    #          #print("arrived at point")
    #          #print(get_signal())
             
    #      else:
    #          time.sleep(0.05)
    #           #simulate the readout while the motor is moving
    
    """
    return 
    

    
def time_estimation(mesh_size_x,mesh_size_y,mesh_size_z,x_length,y_length,z_length,x_speed, y_speed, z_speed):
   
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
    total_distance_z = z_length + (mesh_size_z - z_length % mesh_size_z)  # Ensure it covers the last depth

    # Calculate the time for the scan in each dimension
    time_x = total_distance_x / x_speed
    time_y = total_distance_y / y_speed
    time_z = total_distance_z / z_speed
 
    # estimate of processing time...
    proc = max(x_length,y_length,z_length)/min(mesh_size_x,mesh_size_y,mesh_size_z)
    proc_time = proc*0.1
    
    total_time = time_x + time_y + time_z + proc_time #in seconds
    minutes = total_time/60
    # Return the maximum time as it determines the overall scan time
    return minutes
        
        
        
def get_signal(motor3):
    """returns a dummy signal for a certain amount of time
    
    -if signal drops below a certain value the scan must be paused
    -all 32 channels can be readout at the same time so continuous movement is OK
    -at every point the values are stored in a frequency below 5kHz"""
    data = []
    status3 = motor3.Get(motor3.pv_motor_status)
    while status3 != 0xA:
        print("stuck in this shit")
        data.append(np.random.randint(1000)) #this would correspond to a 
        time.sleep(0.1)  #10Hz measurement frequency
    full_data.append(data)
    

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
    
    
def steps_to_mm(steps,axis): 
    """converts steps to mm for the particular axis i.e. string "1X","1Y" and "2Y" """
    
    if axis == "1X":
        mm = steps/535
    elif axis == "1Y":
        mm = steps/800
    elif axis == "2Y":
        mm = steps/50
    else: print("ERROR, NO VALID AXIS")
    
    return mm
        
def mm_to_steps(mm,axis):
    """converts mm to steps for the particular axis i.e. string "1X","1Y" and "2Y" """
    if axis == "1X":
        steps = mm/535
    elif axis == "1Y":
        steps = mm/800
    elif axis == "2Y":
        steps = mm/50
    else: print("ERROR, NO VALID AXIS")
    
    return steps



# # # # Example usage:
# num_points = 6  # Number of measurement points
# x_length = 21700  # Length of the x-axis
# y_length = 104000 # Length of the y-axis

#measurement_points = distribute_measurement_points(num_points, x_length, y_length)
#points_distribution = snake_grid(num_points,x_length, y_length)
# #plot_measurement_points(measurement_points, x_length, y_length)

# start_scan(1,1,num_points, x_length, y_length,1)