# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 11:49:52 2023

@author: silas
"""

import struct
#from .motor import Module, Motor
#from .reply import Reply, TrinamicException


# MSG_STRUCTURE = ">BBBBIB"
MSG_STRUCTURE = ">BBBBiB"
MSG_STRUCTURE_CAN = ">BBBI"

# REPLY_STRUCTURE = ">BBBBIB"
REPLY_STRUCTURE = ">BBBBiB"
REPLY_STRUCTURE_CAN = ">BBBI"
REPLY_STRUCTURE_IIC = ">BBBIB"

REPLY_LENGTH = 9
REPLY_LENGTH_CAN = 7
REPLY_LENGTH_IIC = 8



#from .bus import Bus
#from .motor import Motor
from commands import Command
#from .reply import Reply
#from .trigger_thread import TriggerThread

#import GUI_leftright as gui


def connect(serial_port, CAN=False): #from init
    return Bus(serial_port, CAN)

class Bus (object): #handles the Datatransmission between chip and program
    #should actually close the port in the right way once the program is done
    def __init__(self, serial, CAN=False):
        self.CAN = CAN
        self.serial = serial

    def send(self, address, command, type, motorbank, value):
        """
        Send a message to the specified module.
        This is a blocking function that will not return until a reply
        has been received from the module.

        See the TMCL docs for full descriptions of the parameters

        :param address:   Module address to send command to
        :param command:   Instruction no
        :param type:	  Type
        :param motorbank: Mot/Bank
        :param value:	  Value

        :rtype: Reply
        """
        if self.CAN:
            msg = struct.pack(MSG_STRUCTURE_CAN, command,
                              type, motorbank, value)
            self.serial.write(msg)
            resp = [0]
            data = self.serial.read(REPLY_LENGTH_CAN)
            resp.extend(struct.unpack(REPLY_STRUCTURE_CAN, data))
            reply = Reply(resp)
            return self._handle_reply(reply)
        else:
            checksum = self._binaryadd(
                address, command, type, motorbank, value)
            msg = struct.pack(MSG_STRUCTURE, int(address), int(command),
                              int(type), int(motorbank), int(value), int(checksum))
            self.serial.write(msg) #here the message is sent
            rep = self.serial.read(REPLY_LENGTH) #here the immediate reply is being read
            reply = Reply(struct.unpack(REPLY_STRUCTURE, rep)) #here the reply is unpacked and made into a readable format
            
            return self._handle_reply(reply)

    def get_module(self, address): #(self, address = 1):
        """
                Returns a Module object targeting the device at address `address`
                You can use this object to retrieve one or more axis motors.

                :param address:
                        Bus address to the target TMCM module
                :type  address: int

                :rtype: Module
        """
        return Module(self, address)

    def get_motor(self, address=1, motor_id=0):#(self, address=1, motor_id=0):
        """
                Returns object addressing motor number `motor_id` on module `address`.
                `address` defaults to 1 (doc for TMCM310 starts counting addresses at 1).
                `motor_id` defaults to 0 (1st axis).

                This is an alias for `get_module(address).get_motor(motor_id)` so that
                backward-compatibility with v1.1.1 is maintained.

                :param address:
                        Bus address of the target TMCM module
                :type  address:  int

                :param motor_id:
                        ID of the motor/axis to target
                :type  motor_id: int

                :rtype: Motor
        """
        return Motor(self, address, motor_id)

    def _handle_reply(self, reply): #handles the reply from the module.
        if reply.status == 100:
            pass
            #print("command succesful")
            #gui.MainWindow.show_message("command succesful") #doesn't work like this... mygui is an instance of the class type mainwindow....
        else:
            print("Problem occured", reply)
        if reply.status < Reply.Status.SUCCESS:
            raise TrinamicException(reply)
        return reply

    def _binaryadd(self, address, command, type, motorbank, value):
        checksum_struct = struct.pack(
            MSG_STRUCTURE[:-1], int(address), int(command), int(type), int(motorbank), int(value))
        checksum = 0
        for s in checksum_struct:
            try:
                checksum += int(s.encode('hex'), 16) % 256
            except:
                checksum += s % 256
            checksum = checksum % 256
        return int(checksum)
    
    
    
from commands import Command
#from .trigger_thread import TriggerThread


class Module(object):
    """
    Represents a single TMCM module present on the bus.
    """

    def __init__(self, bus, address=1):
        """
        :param bus:
                A Bus instance that is connected to one or more
                physical TMCM modules via serial port
        :type  bus: TMCL.Bus

        :param address:
                Module address. This defaults to 1
        :type  address: int

        """
        self.bus = bus
        self.address = address

    def get_motor(self, axis=0):
        """
        Return an interface to a single axis (motor) connected to
        this module.

        :param axis:
                Axis ID (defaults to 0)
        :type axis: int

        :return: An interface to the desired axis/motor
        :rtype:  Motor
        """
        return Motor(self.bus, self.address, axis)


class Motor(object):
    RFS_START = 0
    RFS_STOP = 1
    RFS_STATUS = 2

    def __init__(self, bus, address=1, axis=0):
        self.bus = bus
        self.module_id = address
        self.motor_id = axis
        self.axis = AxisParameterInterface(self)
        self.trigger_thread = None

    def send(self, cmd, type, motorbank, value):
        return self.bus.send(self.module_id, cmd, type, motorbank, value)

    def stop(self):
        if self.trigger_thread is not None:
            try:
                self.trigger_thread.condition_reached.set()
                self.trigger_thread.join()
            except Exception as e:
                pass
        self.send(Command.MST, 0, self.motor_id, 0)

    def get_axis_parameter(self, n):
        reply = self.send(Command.GAP, n, self.motor_id, 0)
        return reply.value

    def set_axis_parameter(self, n, value):
        reply = self.send(Command.SAP, n, self.motor_id, value)
        return reply.value

    def get_user_var(self, n):
        reply = self.send(Command.GGP, n, 2, 0)
        return reply.value

    def set_user_var(self, n, value):
        reply = self.send(Command.SGP, n, 2, value)
        return reply.status

    def rotate_left(self, velocity):
        reply = self.send(Command.ROL, 0, self.motor_id, velocity)
        return reply.status

    def rotate_right(self, velocity):
        reply = self.send(Command.ROR, 0, self.motor_id, velocity)
        return reply.status

    def move_absolute(self, position, callback=None, args=(), kwargs=None):
        reply = self.send(Command.MVP, 0, self.motor_id, position)
        if callback is not None:
            self.trigger_thread = TriggerThread(condition=self.get_position_reached,
                          callback=callback, args=args, kwargs=kwargs)
            self.trigger_thread.start()
        return reply.status

    def move_relative(self, offset, callback=None, args=(), kwargs=None):
        reply = self.send(Command.MVP, 1, self.motor_id, offset)
        if callback is not None:
            self.trigger_thread = TriggerThread(condition=self.get_position_reached,
                          callback=callback, args=args, kwargs=kwargs)
            self.trigger_thread.start()

    def get_position_reached(self):
        return self.axis.target_position_reached

    def run_command(self, cmdIndex):
        reply = self.send(Command.RUN_APPLICATION, 1, self.motor_id, cmdIndex)
        return reply.status

    def reference_search(self, rfs_type):
        reply = self.send(Command.RFS, rfs_type, self.motor_id, 99)
        return reply.status


class AxisParameterInterface(object):
    def __init__(self, motor):
        """

        :param motor:
        :type  motor: Motor
        """
        self.motor = motor

    def get(self, param):
        reply = self.motor.send(Command.GAP, param, self.motor.motor_id, 0)
        return reply.value

    def set(self, param, value):
        reply = self.motor.send(Command.SAP, param, self.motor.motor_id, value)
        return reply.status

     
    def rightstop_readout(self): #can't use the same get because the way i use it in the hardware i use a I/O pin instead of an Axisparameter
        reply = self.motor.send(Command.GIO,1,self.motor.motor_id,0)
        #reply = self.send(Command.MST, 0, self.motor_id, 0)
        return reply.value

    def leftstop_readout(self): #can't use the same get because the way i use it in the hardware i use a I/O pin instead of an Axisparameter
         reply = self.motor.send(Command.GIO,2,self.motor.motor_id,0)
         #reply = self.send(Command.MST, 0, self.motor_id, 0)
         return reply.value

        
    #if i could make it with the designated pins then i would use the provided @property functions. 

    @property
    def target_position(self):
        return self.get(0)

    @target_position.setter
    def target_position(self, value):
        self.set(0, value)

    @property
    def actual_position(self):
        return self.get(1)

    @actual_position.setter
    def actual_position(self, value):
        self.set(1, value)

    @property
    def target_speed(self):
        return self.get(2)

    @target_speed.setter
    def target_speed(self, value):
        self.set(2, value)

    @property
    def actual_speed(self):
        return self.get(3)

    @property
    def max_positioning_speed(self):
        return self.get(4)

    @max_positioning_speed.setter
    def max_positioning_speed(self, value):
        self.set(4, value)

    @property
    def max_accelleration(self):
        return self.get(5)

    @max_accelleration.setter
    def max_accelleration(self, value):
        self.set(5, value)

    @property
    def max_current(self):
        return self.get(6)

    @max_current.setter
    def max_current(self, value):
        self.set(6, value)

    @property
    def standby_current(self):
        return self.get(7)

    @standby_current.setter
    def standby_current(self, value):
        self.set(7, value)

    @property
    def target_position_reached(self):
        return self.get(8)

    @property
    def ref_switch_status(self):
        return self.get(9)

    @property
    def right_limit_status(self):
        return self.get(10)

    @property
    def left_limit_status(self):
        return self.get(11)

    @property
    def right_limit_switch_disabled(self):
        return True if self.get(12) == 1 else False

    @right_limit_switch_disabled.setter
    def right_limit_switch_disabled(self, value):
        self.set(12, 1 if value else 0)

    @property
    def left_limit_switch_disabled(self):
        return True if self.get(13) == 1 else False

    @left_limit_switch_disabled.setter
    def left_limit_switch_disabled(self, value):
        self.set(13, 1 if value else 0)

    @property
    def pulse_divisor(self):
        return self.get(154)

    @pulse_divisor.setter
    def pulse_divisor(self, value):
        self.set(154, value)

    @property
    def ramp_divisor(self):
        return self.get(153)

    @ramp_divisor.setter
    def ramp_divisor(self, value):
        self.set(153, value)

    @property
    def freewheeling_delay(self):
        return self.get(204)

    @freewheeling_delay.setter
    def freewheeling_delay(self, value):
        self.set(204, value)
        
        
class TrinamicException(Exception):
	def __init__( self, reply ):
		super(TrinamicException, self).__init__(Reply.Status.messages[reply.status])
		self.reply = reply


class Reply(object):
	def __init__( self, reply_struct ):
		self.reply_address = reply_struct[0]
		self.module_address = reply_struct[1]
		self.status = reply_struct[2]
		self.command = reply_struct[3]
		self.value = reply_struct[4]
		self.checksum = reply_struct[5]


	class Status(object):
		SUCCESS = 100
		COMMAND_LOADED = 101
		WRONG_CHECKSUM = 1
		INVALID_COMMAND = 2
		WRONG_TYPE = 3
		INVALID_VALUE = 4
		EEPROM_LOCKED = 5
		COMMAND_NOT_AVAILABLE = 6

		messages = {
			1: "Incorrect Checksum",
			2: "Invalid Command",
			3: "Wrong Type",
			4: "Invalid Value",
			5: "EEPROM Locked",
			6: "Command not Available"
		}
        
        
from threading import Thread, Event

# class EndCondition():
#         def __init__(self):
#             #self.bool = False
#             self.running = False
            
#         def get_condition(self):
#             return self.running


# def End(callback=None, args=(), kwargs=None):
#         condition = EndCondition()
#         args = args
#         kwargs = kwargs
#         if callback is not None:
#             TriggerStopThread(condition=condition.get_condition,
#                           callback=callback, args=args, kwargs=kwargs).start()
#             # time.sleep(3)
#             # condition.running = True
        

# def serverstop(arg1, arg2):
#     print(arg1)
#     print(arg2)


# class TriggerStopThread(Thread):
#     """
#     Thread that checks every 0.01 seconds if a condition is reached.
#     When the condition is reached, a callback function will be called.
#     """

#     def __init__(self, stopcondition, callback=None, args=(), kwargs={}):
#         """
#         :condition:
#                 Condition that needs to be reached
#         :callback:
#                 Callback function that should be called, when condition is
#                 reached.
#         :args:
#                 is the argument tuple for the target invocation. Defaults to ().
#         :kwargs:
#                 is a dictionary of keyword arguments for the target
#                 invocation. Defaults to {}.
#         """
#         Thread.__init__(self)
#         if kwargs is None:
#             kwargs = {}
#         self._condition = stopcondition
#         self._callback = callback
#         self._args = args
#         self._kwargs = kwargs
#         self.condition_reached = Event()

#     def run(self):
#         while not self.condition_reached.wait(0.01):
#             if self._condition():
#                 self.condition_reached.set()
#         try:
#             if self._callback:
#                 self._callback(*self._args, **self._kwargs)
#         finally:
#             # Avoid a refcycle if the thread is running a function with
#             # an argument that has a member that points to the thread.
#             del self._callback, self._args, self._kwargs

class TriggerThread(Thread): #is called by move_relative for example to check the movement until the end is reached
    """
    Thread that checks every 0.01 seconds if a condition is reached.
    When the condition is reached, a callback function will be called.
    """

    def __init__(self, condition, callback=None, args=(), kwargs={}):
        """
        :condition:
                Condition that needs to be reached
        :callback:
                Callback function that should be called, when condition is
                reached.
        :args:
                is the argument tuple for the target invocation. Defaults to ().
        :kwargs:
                is a dictionary of keyword arguments for the target
                invocation. Defaults to {}.
        """
        Thread.__init__(self)
        if kwargs is None:
            kwargs = {}
        self._condition = condition
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self.condition_reached = Event()

    def run(self):
        while not self.condition_reached.wait(0.01):
            if self._condition():
                self.condition_reached.set()
        try:
            if self._callback:
                self._callback(*self._args, **self._kwargs)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._callback, self._args, self._kwargs


# if __name__ == "__main__":
#     import time

#     class TestCondition(object):
#         def __init__(self):
#             self.bool = False

#         def get_condition(self):
#             return self.bool

#     def callback(arg1, arg2):
#         print(arg1)
#         print(arg2)

#     def test(callback=None, args=(), kwargs=None):
#         condition = TestCondition()
#         args = args
#         kwargs = kwargs
#         if callback is not None:
#             TriggerThread(condition=condition.get_condition,
#                           callback=callback, args=args, kwargs=kwargs).start()
#             time.sleep(3)
#             condition.bool = True
    

#     test(callback=callback, args=("test1", "test2"))