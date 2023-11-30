# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:50:51 2023

@author: strebe_s
"""

""" in this python script i want to load the array which was saved in the other """

import numpy as np


def load_array_start_calculation(file_path):
    
    data = np.load(file_path, allow_pickle=True)
    
    
    print("the array has been loaded", data[0][0][1][0][0], "and this is the first position")
    print("the array has been loaded", data[1][0][1][0][0], "and this is the first position")