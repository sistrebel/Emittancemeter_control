# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:41:41 2023

@author: strebe_s
"""

"""scanscript which is started from the GUI and uses commands from the communications script with the instances initialized in the GUI when the application itself starts"""

import EPICS_specific_communication as control
import matplotlib.pyplot as plt
from time import time

def distribute_measurement_points(num_points, x_length, y_length):
    if num_points <= 0:
        return []

    points_distribution = []
    for i in range(num_points):
        # Calculate the position of the measurement point
        x = (i % int(num_points**0.5)) * (x_length / int(num_points**0.5))
        y = (i // int(num_points**0.5)) * (y_length / int(num_points**0.5))
        points_distribution.append((x, y))
    
    return points_distribution



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



def start_scan(motor1_queue,motor2_queue,number_of_points,x_length,y_length,server): #this will then issue the commands through the right command queue
    """should start a scan preferably in an independent thread"""
    #get the step distance
    
    #axis length in steps, parameters to adjust for specific situation...
    # x_length = 40000
    # y_length = 5000
    print("number of points", number_of_points)
    
    point_distribution = distribute_measurement_points(number_of_points,x_length,y_length)
    
    for point in point_distribution:
        point_x = point[0]
        point_y = point[1]
        print(point_x,point_y)
        server.issue_motor_command(motor1_queue,("go_to_position",point_x),isreturn = 0)  #moves both motors to the right position
        server.issue_motor_command(motor2_queue,("go_to_position",point_y),isreturn = 0) #the individual threads wait until the motor has moved there
        
        time.sleep(5) #safety
        
        print("go again")
    
    
    #now the scan just needs to move the motors to those step positions one after another
    
    
def pause_scan():
    ...
    


# # Example usage:
num_points = 100  # Number of measurement points
x_length = 50000  # Length of the x-axis
y_length = 4000 # Length of the y-axis

measurement_points = distribute_measurement_points(num_points, x_length, y_length)
#plot_measurement_points(measurement_points, x_length, y_length)

start_scan(1,1,num_points, x_length, y_length,1)