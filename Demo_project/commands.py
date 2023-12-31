# -*- coding: utf-8 -*-
"""
Created on Tue Oct  3 09:30:01 2023

@author: silas
"""

class Command:
	ROL = 2     # Rotate left
	ROR = 1     # Rotate right
	MVP = 4     # Move to position
	MST = 3     # Motor stop
	RFS = 13    # Reference search
	SCO = 30    # Store coordinate
	CCO = 32    # Capture coordinate
	GCO = 31    # Get coordinate
	SAP = 5     # Set axis parameter
	GAP = 6     # Get axis parameter
	STAP = 7    # Store axis parameter into EEPROM
	RSAP = 8    # Restors axis parameter from EEPROM
	SGP = 9     # Set global parameter
	GGP = 10    # Get global parameter
	STGP = 11   # Store global parameter into EEPROM
	RSGP = 12   # Restore global parameter from EEPROM
	SIO = 14    # Set output
	GIO = 15    # Get input
	SAC = 29    # Access to external SPI device
	JA = 22     # Jump always
	JC = 21     # Jump conditional
	COMP = 20   # Compare accumulator with constant value
	CLE = 36    # Clear error flags
	CSUB = 23   # Call subroutine
	RSUB = 24   # Return from subroutine
	WAIT = 27   # Wait for a specified event
	STOP = 28   # End of a TMCL program
	CALC = 19   # Calculate using the accumulator and a constant value
	CALCX = 33  # Calculate using the accumulator and the X register
	AAP = 34    # Copy accumulator to an axis parameter
	AGP = 35    # Copy accumulator to a global parameter
	STOP_APPLICATION = 128
	RUN_APPLICATION = 129
	STEP_APPLICATION = 130
	RESET_APPLICATION = 131
	START_DOWNLOAD_MODE = 132
	QUIT_DOWNLOAD_MODE = 133
	READ_TMCL_MEMORY = 134
	GET_APPLICATION_STATUS = 135
	GET_FIRMWARE_VERSION = 136
	RESTORE_FACTORY_SETTINGS = 137