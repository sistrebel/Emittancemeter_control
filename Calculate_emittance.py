# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:50:51 2023

@author: strebe_s
"""

""" in this python script i want to load the array which was saved in the other """

import numpy as np
import matplotlib.pyplot as plt
from skimage.measure import EllipseModel
from matplotlib import cm
from matplotlib.colors import LightSource
from matplotlib.patches import Ellipse

drift_length = 1200 #in mm, cite Rudolf paper (true for HIPA, not ISTS)

def load_array_start_calculation(file_path, example_array):
    """data has shape (#collimator points, #measurement points per run, 2 {[ waveform values, position triplet]})
     - this function will load the data array, plot the points such that an emittance ellipse can be fitted to it. The determined parameters are then used to calculate the emittance."""
    #data = np.load(file_path, allow_pickle=True)
    
    #data =  np.array(make_array())
    
    data = example_array
    
 
    """the goal would be to calculate the emittance for each section (collimator position of the beam)"""
    

    #calculate the rms of the measurement point by point

    #x part first
    
    channels = [i for i in range(1,161)] 
    angle_x_all = []
    FWHM_x_all = []
    plt.figure()
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm, 0 means on axis
        coll_y = position_triplet[1] 

   
        position_y2 = []
        angle_array_x = [] #will be a list of all rms for each y meas position
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
            
            #convert in into the angle:
            angle_x = np.arctan((rms_x/2)/drift_length)
            
            angle_array_x.append(angle_x) 
            FWHM_array_x.append(FWHM_x)
            position_y2.append(meas_position) #corresponding position to the rms value. 
            
        angle_x_all.append([angle_array_x,position_y2,(coll_x,coll_y)]) #for one collimator position, the rms_values in x at all 
        FWHM_x_all.append([FWHM_array_x,position_y2,(coll_x,coll_y)])
    
    """now i have the array rms_x_all with which i can make the plot (x,p_x) where i have a p_x value for all of the y2 measurement positions!!!"""
    
   
    
    #make an appropriate shape to be able to model it as an ellipse:
    ellipse_arrays_x = []
    for i in range(len(angle_array_x)): #build all the arrays i want and add them to the list
        ellipse_arrays_x.append(np.zeros((len(angle_x_all),2))) #build an array for all the different points at one collimator location
    
    
    for i in range(len(angle_x_all)):
        for j in range(len(angle_x_all[i][0])):
            
            ellipse_arrays_x[j][i][0] = angle_x_all[i][2][0] #x
            ellipse_arrays_x[j][i][1] = angle_x_all[i][0][j] #p_x
   
    
   
    #make the (x,px) plots for each measurement position y2 there will be one
    plt.figure()
    plt.grid()
    for point in angle_x_all: #iterate through all the collimator points in 
        
        coll_x = point[2][0]
        coll_y = point[2][1]
        
        angle_array_x_plus = point[0] #sigma+ stuff
        angle_array_x_minus = -np.array(point[0]) #sigma- stuff (just mirrored)
        
        #make an array with coll_x position in it of length rms_array_x
        coll_x_arr = [coll_x for i in range(len(angle_array_x))]
        
        plt.scatter(coll_x_arr, angle_array_x_plus)
        plt.scatter(coll_x_arr, angle_array_x_minus)
        
        

        
    #(y,p_y) part
    angle_y_all = []
    FWHM_y_all = []
    plt.figure()
    for i in range(0, len(data)): #each collimator point separately
        position_triplet = data[i][0][1]
        coll_x = position_triplet[0] #in mm, 0 means on axis
        coll_y = position_triplet[1] #fix this position for now, we iterate over all points who lay in one line i.e. who simulate the slit...
        
        
        angle_array_y = [] #will be a list of all rms for each y meas position
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
            
            #convert this into angles who do not depend on drift length then
            angle_y = np.arctan((rms_y/2)/drift_length)
            
            angle_array_y.append(angle_y) 
       
            plt.plot(position_y2, distribution)    
        
        FWHM_y_all.append([FWHM_array_y,channels,(coll_x,coll_y)])
        angle_y_all.append([angle_array_y,channels,(coll_x,coll_y)]) #for one collimator position, the rms_values in x at all 
    
    
    
    #make an appropriate shape to be able to model it as an ellipse:
    ellipse_arrays_y = []
    for i in range(len(angle_array_y)): #build all the arrays i want and add them to the list
        ellipse_arrays_y.append(np.zeros((len(angle_y_all),2))) #build an array for all the different points at one collimator location
    
    
    for i in range(len(angle_y_all)):
        for j in range(len(angle_y_all[i][0])):
        
            ellipse_arrays_y[j][i][0] = angle_y_all[i][2][1] #y
            ellipse_arrays_y[j][i][1] = angle_y_all[i][0][j] #p_y
    
    #make the (x,px) plots for each measurement position y2 there will be one
    plt.figure()
    plt.grid()
    for point in angle_y_all: #iterate through all the collimator points in 
        
    
        coll_x = point[2][0]
        coll_y = point[2][1]
        
        
        angle_array_y_plus = point[0] #sigma+ stuff
        angle_array_y_minus = -np.array(point[0]) #sigma- stuff (just mirrored)
        
        #make an array with coll_x position in it of length rms_array_x
        coll_y_arr = [coll_y for i in range(len(angle_array_y))]
        
        plt.scatter(coll_y_arr, angle_array_y_plus)
        plt.scatter(coll_y_arr, angle_array_y_minus)
    
        

    
    """now i want to turn the points into  a "2D numpy array" where each row is a point [x,p_x]. Then i pass this to the fitting function and this will then return the ellipse model i want"""
    
    
    # ellipse_array = ellipse_arrays_y[49]
    # ellipse_model = fit_ellipse_to_points(ellipse_array)
    # plot_ellipse_and_points(ellipse_model, ellipse_array)
    # emittance = estimate_ellipse_area(ellipse_model)
    
    """
   #fit ellipse to it and estimate area... 
    
    emittances_y = []
    for ellipse_array in ellipse_arrays_y:
        ellipse_model = fit_ellipse_to_points(ellipse_array)
        plot_ellipse_and_points(ellipse_model, ellipse_array)
        
        emittance = estimate_ellipse_area(ellipse_model)
        emittances_y.append(emittance)
    
    emittances_x = []
    
    
    for ellipse_array in ellipse_arrays_x:
        ellipse_model = fit_ellipse_to_points(ellipse_array)
        plot_ellipse_and_points(ellipse_model, ellipse_array)
   
        
        emittance = estimate_ellipse_area(ellipse_model)
        emittances_x.append(emittance)
    """
    
    
def estimate_ellipse_area(ellipse_model):
    """
    Estimate the area of an ellipse using its parameters.

    Parameters:
    - ellipse_model: EllipseModel object containing the parameters of the ellipse.

    Returns:
    - area: Estimated area of the ellipse.
    """
    if ellipse_model is None:
        raise ValueError("Ellipse model is None. Cannot estimate area.")

    major_axis_length = ellipse_model.params[2]# * 2
    minor_axis_length = ellipse_model.params[3]# * 2

    area = np.pi * major_axis_length * minor_axis_length
    emittance = area/np.pi
    return emittance

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
    
        print ("At least 5 points are required for ellipse fitting.")
        return None
    
    # Fit an ellipse to the points
    ellipse_model = EllipseModel()
    try:
        ellipse_model.estimate(points)
    except Exception as e:
        print(f"Error: {e}")
    return ellipse_model    
    
def plot_ellipse_and_points(ellipse_model, points):
    """
    Plot the fitted ellipse and the input points.

    Parameters:
    - ellipse_model: EllipseModel object containing the parameters of the fitted ellipse.
    - points: A 2D NumPy array or list of points, where each row is a point [x, y].
    """
    if ellipse_model is None:
        print("Ellipse model is None. Cannot plot.")
        return

    fig, ax = plt.subplots()

    # Plot the points
    ax.scatter(points[:, 0], points[:, 1], label='Points', color='blue')

    # Plot the fitted ellipse using matplotlib.patches.Ellipse
    ellipse = Ellipse(
        xy=ellipse_model.params[:2],  # Center
        width=ellipse_model.params[2] * 2,  # Major axis length
        height=ellipse_model.params[3] * 2,  # Minor axis length
        angle=np.degrees(ellipse_model.params[4]),  # Rotation angle in degrees
        fill=False,
        color='red',
        label='Fitted Ellipse'
    )
    ax.add_patch(ellipse)

    ax.set_aspect('equal', adjustable='box')  # Ensure equal aspect ratio
    ax.legend()
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Fitted Ellipse to Points')
    
    plt.show()
   

def FWHM(X,Y):
    """Determines the Full width at half maximum of a distribution of points [X,Y] and returns it if possible
    !!!NOT FINISHED!!!"""
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
    """Creates an example array of the desired shape with random entries"""
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



if __name__ == "__main__":

    
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
               0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -120.0, 41.78]]
    
    x = [np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
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
               0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -130.0, 41.78]]
    
    x3 = [np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
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
               0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -140.0, 41.78]]
    
    x4 = [np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
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
               0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -150.0, 41.78]]
    
    
    x5 = [np.array([    0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.,
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
               0.,     0.,     0.,     0.,     0.,     0.,     0.,     0.]), [6.833333333333332, -160.0, 41.78]]


    
    
    
    example_array = np.array([x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x], dtype=object)
    example_array2 = np.array([x2,x2,x2,x2,x,x2,x2,x2,x2,x,x,x,x2,x2,x2,x2,x2,x2], dtype=object) #measurement points of MWE2Y
    example_array3 = np.array([x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3,x3], dtype=object)
    example_array4 = np.array([x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4,x4], dtype=object)
    example_array5 = np.array([x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5,x5], dtype=object)
    example_array_full = np.array([example_array,example_array2,example_array3,example_array3, example_array4], dtype=object) #at several collimator points...
    
    load_array_start_calculation("hi", example_array_full)
    #load_array_start_calculation("ho", make_array())