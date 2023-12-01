# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:50:51 2023

@author: strebe_s
"""

""" in this python script i want to load the array which was saved in the other """

import numpy as np


drift_length = 1200 #in mm, cite Rudolf paper (true for HIPA, not ISTS)

def load_array_start_calculation(file_path):
    """data has shape (#collimator points, #measurement points per run, 2 {[ waveform values, position triplet]})"""
    data = np.load(file_path, allow_pickle=True)
    
    print("the shape iss" ,data.shape)
    
    print("the array has been loaded", data[0][0][1][0], "and this is the first position")
    print("the array has been loaded", data[0][1][1][0], "and this is the first position")
    print(data[0][0][0])
    print(data[0][0][1])
    
    """the goal would be to calculate the emittance for each section (collimator position of the beam)"""
    
    
    #calculate the rms of the measurement point by point
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm from 0
        coll_y = position_triplet[1] #in mm from 0
        
        for j in range(0,len(data[i])):
            meas_position = data[i][j][1][2] #position of the readout stack in y, in mm from ccw
            
            delta_y = abs(coll_y - meas_position)
            
            
    distribution = data
    rms = np.sqrt(np.mean(np.square(distribution)))



