# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 16:00:37 2023

@author: strebe_s
"""



import matplotlib.pyplot as plt
import numpy as np


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