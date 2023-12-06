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

def load_array_start_calculation(file_path, example_array):
    """data has shape (#collimator points, #measurement points per run, 2 {[ waveform values, position triplet]})"""
    #data = np.load(file_path, allow_pickle=True)
    
    #data =  np.array(make_array())
    
    data = example_array
    
    print("the shape iss" ,data.shape)
    
    print("the array has been loaded", data[0][0][1][0], "and this is the first position")
    print("the array has been loaded", data[0][1][1][0], "and this is the first position")
    print(data[0][0][0])
    print(data[0][0][1])
    
    """the goal would be to calculate the emittance for each section (collimator position of the beam)"""
    

    #calculate the rms of the measurement point by point
    
    # first_term = 0 #<x^1>
    # second_term = 0 #<x'^2>
    # third_term = 0 #<xx'^2>
    
    #x part first
    
    channels = [i for i in range(1,161)] 
    rms_x_all = []
    FWHM_x_all = []
    plt.figure()
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm, 0 means on axis
        coll_y = position_triplet[1] 

   
        position_y2 = []
        rms_array_x = [] #will be a list of all rms for each y meas position
        FWHM_array_x = []
        for j in range(0,len(data[i])):
            meas_position = data[i][j][1][2] #position of the readout stack in y, in mm 0 means on axis. 
    
            #get the distribution of the of the measurement that is done in x as an rms:
        
            distribution = data[i][j][0] #should be those 160 values
            #plt.figure()
            plt.plot(channels, distribution)
            
            FWHM_x = FWHM(channels, distribution)/2 #only take one side of the FWHM (i will need two points later, it's symmetric anyway...)
            #FWHM_x*2*np.log(2)
            
            rms_x = np.sqrt(np.mean(np.square(distribution))) #rms divergence of the j-th measurment position in y for the i-th collimator position
            
            rms_array_x.append(rms_x) 
            FWHM_array_x.append(FWHM_x)
            position_y2.append(meas_position) #corresponding position to the rms value. 
            
        rms_x_all.append([rms_array_x,position_y2,(coll_x,coll_y)]) #for one collimator position, the rms_values in x at all 
        FWHM_x_all.append([FWHM_array_x,position_y2,(coll_x,coll_y)])
    
    """now i have the array rms_x_all with which i can make the plot (x,p_x) where i have a p_x value for all of the y2 measurement positions!!!"""
    
    #make the (x,px) plots for each measurement position y2 there will be one
    plt.figure()
    plt.grid()
    
    ellipse_array_x = np.zeros((len(rms_x_all),2))
    for point in rms_x_all: #iterate through all the collimator points in 
        
        coll_x = point[2][0]
        coll_y = point[2][1]
        
        rms_array_x_plus = point[0] #sigma+ stuff
        rms_array_x_minus = -np.array(point[0]) #sigma- stuff (just mirrored)
        
        #make an array with coll_x position in it of length rms_array_x
        coll_x_arr = [coll_x for i in range(len(rms_array_x))]
        
        plt.scatter(coll_x_arr, rms_array_x_plus)
        plt.scatter(coll_x_arr, rms_array_x_minus)
        
        

        
    #(y,p_y) part
    rms_y_all = []
    FWHM_y_all = []
    plt.figure()
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm, 0 means on axis
        coll_y = position_triplet[1] #fix this position for now, we iterate over all points who lay in one line i.e. who simulate the slit...
        
        
        rms_array_y = [] #will be a list of all rms for each y meas position
        FWHM_array_y = []
        for k in range(0,len(channels)):#build up the distribution for a fixed channel first
            channel = channels[k]
            
            
            distribution = [] #fill the distribution for this channel into this array
            for j in range(0,len(data[i])): #number of measurement points in y2
                meas_position = data[i][j][1][2] #position of the readout stack in y, in mm 0 means on axis. 
                #get the distribution of the of the measurement that is done in x as an rms:
        
                distribution.append(data[i][j][0][k]) #adds the value of the k-th channel and the j-th meas point in y2 into the distr
                
                
            FWHM_y = FWHM(position_y2, distribution)/2 #only one side of it
            #FWHM_y*2*np.log(2)
            
            FWHM_array_y.append(FWHM_y)
            rms_y = np.sqrt(np.mean(np.square(distribution))) #rms divergence of the j-th measurment position in y for the i-th collimator position
            rms_array_y.append(rms_y) 
              #corresponding position to the rms value. 
        #plt.figure()
            #print(distribution)
            plt.plot(position_y2, distribution)    
        
        FWHM_y_all.append([FWHM_array_y,channels,(coll_x,coll_y)])
        rms_y_all.append([rms_array_y,channels,(coll_x,coll_y)]) #for one collimator position, the rms_values in x at all 
    
    #make the (x,px) plots for each measurement position y2 there will be one
    plt.figure()
    plt.grid()
    
    ellipse_arrays_y = []
    for i in range(len(rms_array_y)): #build all the arrays i want and add them to the list
        ellipse_arrays_y.append(np.zeros((len(rms_y_all),2))) #build an array for all the different points at one collimator location
    
    
    i = 0
    for point in rms_y_all: #iterate through all the collimator points in 
        
    
        coll_x = point[2][0]
        coll_y = point[2][1]
        
        
        
        rms_array_y_plus = point[0] #sigma+ stuff
        rms_array_y_minus = -np.array(point[0]) #sigma- stuff (just mirrored)
        
        #make an array with coll_x position in it of length rms_array_x
        coll_y_arr = [coll_y for i in range(len(rms_array_y))]
        
        plt.scatter(coll_y_arr, rms_array_y_plus)
        plt.scatter(coll_y_arr, rms_array_y_minus)
    
        
    
    """now i want to turn the points into  a "2D numpy array" where each row is a point [x,p_x]. Then i pass this to the fitting function and this will then return the ellipse model i want"""
        
    

def FWHM(X,Y):
    half_max = max(Y) / 2.
    #find when function crosses line half_max (when sign of diff flips)
    #take the 'derivative' of signum(half_max - Y[])
    d = np.sign(half_max - np.array(Y[0:-1])) - np.sign(half_max - np.array(Y[1:]))
    #plot(X[0:len(d)],d) #if you are interested
    #find the left and right most indexes
    left_idx = np.where(d > 0)[0]
    right_idx = np.where(d < 0)[-1]
    try:
        return X[right_idx[0]] - X[left_idx[0]] #return the difference (full width)
    except:
        return 0
  

def make_array():
    array = []
    coll_points = 10
    meas_points = 16
    for i in range(0,coll_points):
        part_array =[]
        for j in range(0,meas_points):
            distr = np.random.rand(160)
            pos = np.random.rand(3)
            part_array.append([distr,pos])
        array.append(part_array)
    return np.array(array,dtype=object)

#array = np.array(make_array())





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


from skimage.measure import EllipseModel

def fit_ellipse_to_points(points):
    """
    Fit an ellipse to a set of 2D points.

    Parameters:
    - points: A 2D NumPy array or list of points, where each row is a point [x, y].

    Returns:
    - ellipse_model: EllipseModel object containing the parameters of the best-fitted ellipse.
    """
    points = np.array(points)
    
    # Ensure at least 5 points are provided for the ellipse fitting
    if len(points) < 5:
        raise ValueError("At least 5 points are required for ellipse fitting.")
    
    # Fit an ellipse to the points
    ellipse_model = EllipseModel()
    ellipse_model.estimate(points)

    return ellipse_model

# Example usage:
# Replace this with your actual set of points
sample_points = np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]])

# Fit ellipse to the sample points
fitted_ellipse = fit_ellipse_to_points(sample_points)

# Display the fitted ellipse parameters
print("Fitted Ellipse Parameters:")
print("Center:", fitted_ellipse.params[0:2])
print("Axes Lengths:", fitted_ellipse.params[2:4])
print("Rotation Angle (radians):", fitted_ellipse.params[4])

    



x2 = [np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     31130.,     31530., 32830.,
           38730.,     31530.,     31130.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0., 0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -125.0, 4.78]]

x = [2*np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     31130.,     31530., 31830.,
           31730.,     31530.,     31130.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0., 0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [4.833333333333332, -122.0, 41.78]]

x3 = [2*np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     31130.,     31530., 37830.,
           39730.,     31530.,     31130.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0., 0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,  0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
           0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [4.33333333333332, -120.0, 41.78]]


example_array = np.array([x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x], dtype=object)
example_array2 = np.array([x2,x2,x2,x2,x,x2,x2,x2,x2,x,x,x,x2,x2,x2,x,x,x], dtype=object) #measurement points of MWE2Y
example_array3 = np.array([x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3], dtype=object)
example_array_full = np.array([example_array,example_array2,example_array2,example_array3, example_array3], dtype=object) #at several collimator points...

#load_array_start_calculation("hi", example_array_full)
#load_array_start_calculation("ho", make_array())