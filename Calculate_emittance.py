# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:50:51 2023

@author: strebe_s
"""

""" in this python script i want to load the array which was saved in the other """

import numpy as np

import matplotlib.pyplot as plt
 

from matplotlib import cbook, cm
from matplotlib.colors import LightSource


drift_length = 1200 #in mm, cite Rudolf paper (true for HIPA, not ISTS)

def load_array_start_calculation(file_path):
    """data has shape (#collimator points, #measurement points per run, 2 {[ waveform values, position triplet]})"""
    #data = np.load(file_path, allow_pickle=True)
    
    data =  np.array(make_array())
    print("the shape iss" ,data.shape)
    
    print("the array has been loaded", data[0][0][1][0], "and this is the first position")
    print("the array has been loaded", data[0][1][1][0], "and this is the first position")
    print(data[0][0][0])
    print(data[0][0][1])
    
    """the goal would be to calculate the emittance for each section (collimator position of the beam)"""
    
    
    #get mean slit position in x and y
    #get mean div of j-th beamlet and the same for all beamlets
    
    
    #calculate the rms of the measurement point by point
    rms_values = []
    first_term = 0 #<x^1>
    second_term = 0 #<x'^2>
    third_term = 0 #<xx'^2>
    
    channels = [i for i in range(1,33)] 
    
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm, 0 means on axis
        coll_y = position_triplet[1] #fix this position for now, we iterate over all points who lay in one line i.e. who simulate the slit...
        
        rms_array = [] #will be a list of all rms for each y meas position
        for j in range(0,len(data[i])):
            meas_position = data[i][j][1][2] #position of the readout stack in y, in mm 0 means on axis. 
            
            delta_y = abs(coll_y - meas_position)
            
            
            
            
            #if delta_y < 0.1: #then we want to read out (if it's basically in allignement)
            #get the distribution of the of the measurement that is done in x as an rms:
            
                
            distribution = data[i][j][0] #should be those 32 values
            plt.plot(channels, distribution)
            
            np.max(distribution)
    
            rms = np.sqrt(np.mean(np.square(distribution))) #rms divergence of the j-th measurment position in y for the i-th collimator position
            rms_array.append(rms)
            std = np.std(distribution)
            
            rms_xj_sq = np.square(rms/drift_length)  
            
            #getting the terms in equation (30) of Min Zhang. Emittance Formula for Slits and Pepperpot Measurement. FERMILAB-TM-1988
            #first_term += ...
            #second_term += ...
            #third_term += ...
            
        rms_values.append(rms_array) #will be an array of all rms arrays for each collimator position

    print(rms_values[1][1])


def make_array():
    array = []
    coll_points = 100
    meas_points = 30
    for i in range(0,coll_points):
        part_array =[]
        for j in range(0,meas_points):
            distr = np.random.rand(32)
            pos = np.random.rand(3)
            part_array.append([distr,pos])
        array.append(part_array)
    return array

#array = np.array(make_array())

load_array_start_calculation("hi")


def distribution_plot(data):
    """with the full dataset at one collimator point make a 3D-plot of the measured intesities"""

# Load and format data
    y_meas = []
    z_meas = []
    for i in range(0, len(data)):
        y_meas.append(data[i][1][2])
        z_meas.append(data[i][0])
    x_meas = np.arange(1,33,1)
        
    # z = dem['elevation']
    # nrows, ncols = z.shape
    # x = np.linspace(dem['xmin'], dem['xmax'], ncols)
    #y = np.linspace(dem['ymin'], dem['ymax'], nrows)
    x, y = np.meshgrid(x_meas, y_meas)

#region = np.s_[5:50, 5:50]
#x, y, z = x_meas[region], y_meas[region], zmeas[region]

    # Set up plot
    fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))
    
    ls = LightSource(270, 45)
    # To use a custom hillshading mode, override the built-in shading and pass
    # in the rgb colors of the shaded surface calculated from "shade".
    rgb = ls.shade(np.array(z_meas), cmap=cm.gist_earth, vert_exag=0.1, blend_mode='soft')
    surf = ax.plot_surface(x_meas, y_meas, np.array(z_meas), rstride=1, cstride=1, facecolors=rgb,
                           linewidth=0, antialiased=False, shade=False)

    plt.show()

# data =  np.array(make_array())
# distribution_plot(data[2])