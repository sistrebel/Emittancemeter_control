# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:50:51 2023

@author: strebe_s
"""

""" in this python script i want to load the array which was saved in the other """

import numpy as np


def load_array_start_calculation(file_path):
    """data has shape (#collimator points, #measurement points per run, 2 {[ waveform values, position triplet]})"""
    data = np.load(file_path, allow_pickle=True)
    
    print("the shape iss" ,data.shape)
    
    print("the array has been loaded", data[0][0][1][0], "and this is the first position")
    print("the array has been loaded", data[0][1][1][0], "and this is the first position")
    print(data[0][0][0])
    print(data[0][0][1])
    
    """the goal would be to calculate the emittance for each section (collimator position of the beam)"""