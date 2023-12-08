# -*- coding: utf-8 -*-
"""
Created on Thu Dec  7 16:21:06 2023

@author: strebe_s
"""


from epics import PV
import numpy as np
import scan_script as scan
import time
import datetime
import Calculate_emittance

class Measurement():
    """is the measurement device for all LogIV cards. """
    
    def __init__(self, server): 
        """setup all the process variables that will be needed"""
        self.full_data = [] #this is where the measurement is stored
        
        #waveform of the data
        self.pv_IA_wave = PV('T-MWE2IA:PROF:1')#PV('MWE2IA:PROF:1') #similar to this at least, each one possible to read 32 channels 
        self.pv_IB_wave = PV('T-MWE2IA:PROF:1') #!!!!!!!!!!!!!!!!!!! MUST CHANGE THOSE TO THE RIGHT PV'S ONCE THE FULL SETUP IS THERE!!!!!!!!!!!!!!!!!
        self.pv_IC_wave = PV('T-MWE2IA:PROF:1')
        self.pv_ID_wave = PV('T-MWE2IA:PROF:1')
        self.pv_IE_wave = PV('T-MWE2IA:PROF:1')
        
        
    def get_signal(self,motor3,goinsteps,meas_freq,point_z,point_x,point_y,endpoint_z):
        """captures the signal from the 160 channels with a rate of meas_freq and stores it in the full_data array
    
        -if signal drops below a certain value the scan must be paused
        -all 32 channels can be readout at the same time so continuous movement is OK, actually there are 160 channels, 32 per card.
        -at every point the values are stored in a frequency below 5kHz"""
        
        allchannels_onepoint = [] #will have the shape [[[160 values], position],
    
        
        
        if goinsteps == False:
            status3 = motor3.Get(motor3.pv_motor_status)
            point_z = motor3.Get(motor3.pv_SOLRB)
            
            
            while point_z != endpoint_z and status3 != 0xA and scan.scanstop == False:
                
                """get the postition of readout, assuming the delay is small enough such that the position remain approx. the same..."""
                point_z = motor3.Get(motor3.pv_SOLRB) #get the postition of readout, assuming the delay is small enough such that the position remain approx. the same...
        
                status3 = motor3.Get(motor3.pv_motor_status)
                waveform_IA = np.array(self.pv_IA_wave.get()) #is a list of 32 values
                waveform_IB = np.array(self.pv_IB_wave.get())
                waveform_IC = np.array(self.pv_IC_wave.get())
                waveform_ID = np.array(self.pv_ID_wave.get())
                waveform_IE = np.array(self.pv_IE_wave.get()) 
                
                #merge them together as there are actually 160 channels side by side
                full_waveform_temp = np.concatenate((waveform_IA ,waveform_IB ,waveform_IC ))
                full_waveform = np.concatenate((full_waveform_temp , waveform_ID , waveform_IE))
                
            
                current_position = [point_x,point_y,point_z] #positons of the motors in steps... 
                
                #convert those to positions in mm
                current_position_mm = [scan.steps_to_mm(point_x,"1X"),scan.steps_to_mm(point_y,"1Y"),scan.steps_to_mm(point_z,"2Y")]
                
                allchannels_onepoint.append([full_waveform,current_position_mm])
   
    
                time.sleep(1/meas_freq) #measurement frequency
                
        if goinsteps:
            current_position = [point_x,point_y,point_z] #positons of the motors in steps...
            current_position_mm = [scan.steps_to_mm(point_x,"1X"),scan.steps_to_mm(point_y,"1Y"),scan.steps_to_mm(point_z,"2Y")]
            
            #for i in range(0,int(meas_freq)): #could use this to measure several times at one position..., not necessary though, use one measurement for now
                    
            waveform_IA = self.pv_IA_wave.get() #is a list of 32 values, takes one second
            waveform_IB = self.pv_IB_wave.get()
            waveform_IC = self.pv_IC_wave.get()
            waveform_ID = self.pv_ID_wave.get()
            waveform_IE = self.pv_IE_wave.get()
            
            #merge them together as there are actually 160 channels side by side
            full_waveform = waveform_IA + waveform_IB +waveform_IC + waveform_ID + waveform_IE
            
          
            allchannels_onepoint.append([full_waveform,current_position_mm])
                    
            #time.sleep(1/meas_freq)
        
        
        self.full_data.append(allchannels_onepoint)
    
        
    def handle_and_save_data(self,path):
        """saves the full_data array into a file and handles the format
        
        self.full_data.shape == (#positions,#measurements,[[32 values],[posx,posy,posz]])
        
        """
        if self.full_data != []:
            larger_nested_array = self.full_data
            # Save the larger nested array to a .npy file
            if path != "":
                file_path = path #+ 'scan_array'+ str(datetime.datetime.now())+'.npy'
            else:
                file_path = 'scan_array'+ str(datetime.datetime.now())+'.npy' #saves it to the same place where the program is saved
            np.save(file_path, larger_nested_array)

        Calculate_emittance.load_array_start_calculation(file_path)
        
        # # Load the array back
        # loaded_nested_array = np.load(file_path)

        # # Print the shape of the loaded array
        # print("Shape of the loaded array:", loaded_nested_array.shape)