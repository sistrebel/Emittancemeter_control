# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:41:41 2023

@author: strebe_s
"""

"""scanscript which is started from the GUI and uses commands from the communications script with the instances initialized in the GUI when the application itself starts"""

import EPICS_specific_communication as control
import matplotlib.pyplot as plt
import time
import numpy as np
import datetime
import Measurement_script 

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
    
    number_of_points = calculate_mesh_points_2d(meshsize_x, meshsize_y, x_length,y_length)
    message_queue.put(">> number of points: " + str(number_of_points))
    
    #runtime estimation in minutes
    estimated_time = time_estimation(goinsteps,meshsize_x,meshsize_y,meshsize_z,x_length,y_length,z_length,x_speed, y_speed, z_speed, number_of_points)
    
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
    
    
    point_distribution = snake_grid(number_of_points,x_length,y_length)
    
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
        
"""----- Service functions --------------------------------------------------------------------------------------------------------------------------------------------------------------"""


def time_estimation(goinsteps,mesh_size_x,mesh_size_y,mesh_size_z,x_length,y_length,z_length,x_speed, y_speed, z_speed,number_of_points):
   
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
    - float: The estimated time for the scan in minutes.
    """
    # Calculate the total distance in each dimension
    total_distance_x = x_length + (mesh_size_x - x_length % mesh_size_x)  # Ensure it covers the last row
    total_distance_y = y_length + (mesh_size_y - y_length % mesh_size_y)  # Ensure it covers the last column
   
    total_distance_z = number_of_points*(2*z_length + (mesh_size_z - z_length % mesh_size_z))  # Ensure it covers the last depth

    # Calculate the time for the scan in each dimension
    time_x = total_distance_x / x_speed
    time_y = total_distance_y / y_speed
    time_z = total_distance_z / z_speed
    
    if goinsteps:
        time_z_added = (z_length/mesh_size_z)*number_of_points*1 #add a second for everytime it needs to accelerate/brake.
        time_z += time_z_added
 
    # estimate of processing time...
    proc = max(x_length,y_length,z_length)/min(mesh_size_x,mesh_size_y,mesh_size_z) #worst number of commands needed to process
    proc_time = proc*2 #times 2 seconds
    
    total_time = time_x + time_y + time_z + proc_time #in seconds
    minutes = round(total_time/60,2)
    # Return the maximum time as it determines the overall scan time
    return minutes

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


    
    
def steps_to_mm(steps,axis,isspeed=False): 
    """converts steps to mm for the particular axis i.e. string "1X","1Y" and "2Y" """
    """The mapped_mm depends on the allignement..."""
    
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
    """The mapped_steps depends on the allignement..."""
    
    
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