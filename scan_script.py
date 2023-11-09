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

def distribute_measurement_points(num_points, x_length, y_length):
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


def snake_grid(num_points, x_lenght,y_length):
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
    # print(grid_points)
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



def start_scan(motor1,motor2,motor3,number_of_points,x_length,y_length,server): #this will then issue the commands through the right command queue
    """should start a scan preferably in an independent thread"""
    
    #start with recalibration of the motors:
    server.issue_motor_command(motor1.command_queue,("calibrate",),isreturn = 0)
    server.issue_motor_command(motor2.command_queue,("calibrate",),isreturn = 0)
    server.issue_motor_command(motor3.command_queue,("calibrate",),isreturn = 0)
    
    while motor1.iscalibrating == True or motor2.iscalibrating == True: #or motor3.iscalibrating == True: #wait for calibration to be done
        time.sleep(0.1)
    #axis length in steps, parameters to adjust for specific situation...
    # x_length = 40000
    # y_length = 5000
    print("number of points", number_of_points)
    
    #set the desired scan speed
    x_speed = 1000
    y_speed = 1000
    server.issue_motor_command(motor1.command_queue,("set_speed",x_speed),isreturn = 0)
    server.issue_motor_command(motor2.command_queue,("set_speed",y_speed),isreturn = 0)
    
    point_distribution = snake_grid(number_of_points,x_length,y_length)
    print(point_distribution)
    
    #old_point = [0,0] #starting point, both motors parked at '0'
    
    for i in range(len(point_distribution)):
        if server.running == True:  #check that QtApplication has not been closed
            point_x = point_distribution[i][0]
            point_y = point_distribution[i][1]
            print(point_x,point_y)
            
            
            #estimate the time it takes to move from current position to target position here
            #time_needed = time_estimation(old_point, new_point, x_speed, y_speed)
            
        
            moving = False
            while moving == False: #wait till motors are free and stopped
                if motor1.ismoving == False and  motor2.ismoving == False:  #check that motors are actually free to move
                    server.issue_motor_command(motor1.command_queue,("go_to_position",point_x),isreturn = 0)  #moves motor on thread one
                    server.issue_motor_command(motor2.command_queue,("go_to_position",point_y),isreturn = 0) #moves motor on thread two
                    moving = True
                else: time.sleep(0.2)
            #time.sleep(time_needed)
            
            while moving == True: #wait until motors are done moving
                if motor1.ismoving == True or motor2.ismoving == True:  #check that motors are actually free to move
                    time.sleep(0.2)
                else:
                    moving = False 
                    print("arrived at point")
           
            
            result = start_readout(motor3,server)
            
            print(result)
            
            #return to initial position
            return_speed = 1000
            server.issue_motor_command(motor3.command_queue,("go_to_position",return_speed),isreturn = 0)
            
            #old_point = new_point 
            
            
            print("go again")
        else:
            print("ERROR: GUI/server has been closed")
            
    
    print("scan is done")
    
    
    
    
def start_readout(motor3,server):
    """does readout stuff"""
    readout_speed = 1000
    server.issue_motor_command(motor3.command_queue,("set_speed",readout_speed),isreturn = 0)
    
    end_point = 1000
    start_point = 0
    
    #time_needed = time_estimation(start_point, end_point, readout_speed,readout_speed)
    
    moving = False
    while moving == False: #wait till motors are free and stopped
        if motor3.ismoving == False:  #check that motors are actually free to move, readjusting takes time as well
            server.issue_motor_command(motor3.command_queue,("go_to_position",end_point),isreturn = 0)
            moving = True
        else: time.sleep(0.2)
    #time.sleep(time_needed)
    
    while moving == True: #wait until motors are done moving
        if motor3.ismoving == True:  #check that motors are actually free to move
            time.sleep(0.1)
            print(get_signal()) #simulate the readout while the motor is moving
        else:
            moving = False 
            print("arrived at point")
    
    return "readout done"
    

    
def time_estimation(old_points, new_points, x_speed,y_speed):
        time_needed_x = abs(new_points[0] - old_points[0])/x_speed
        time_needed_y = abs(new_points[1] - old_points[1])/y_speed
        
        if time_needed_x > time_needed_y:
            return time_needed_x + 0.5 #add artificial value for safety...
        else:
            return time_needed_y + 0.5
        
        
def get_signal():
    """returns a dummy signal for a certain amount of time"""
    return np.random.randint(1000)
    
    
    
def pause_scan():
    """when the pause button is clicked on the GUI the scan procedure should pause and not go to the next point"""
    ...
    
    
def steps_to_mm(steps,axis): 
    """converts steps to mm for the particular axis i.e. string "1X","1Y" and "2Y" """
    
    if axis == "1X":
        mm = steps/535
    if axis == "1Y":
        mm = steps/800
    if axis == "2Y":
        mm = steps/50
    else: print("ERROR, NO VALID AXIS")
    
    return mm
        
def mm_to_steps(mm,axis):
    """converts mm to steps for the particular axis i.e. string "1X","1Y" and "2Y" """
    if axis == "1X":
        steps = mm/535
    if axis == "1Y":
        steps = mm/800
    if axis == "2Y":
        steps = mm/50
    else: print("ERROR, NO VALID AXIS")
    
    return steps



# # # Example usage:
num_points = 100  # Number of measurement points
x_length = 21700  # Length of the x-axis
y_length = 104000 # Length of the y-axis

#measurement_points = distribute_measurement_points(num_points, x_length, y_length)
points_distribution = snake_grid(num_points,x_length, y_length)
# #plot_measurement_points(measurement_points, x_length, y_length)

# start_scan(1,1,num_points, x_length, y_length,1)