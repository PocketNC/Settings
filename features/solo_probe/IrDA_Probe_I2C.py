#! /usr/bin/python3

"""
This Module interacts over I2C with a microcontroller to drive Addressable LED strips
"""

import time
import binascii

class Probe_COMMANDS():
    """This holds all of the commands and lookup values for the Probe Status."""
    def __init__(self):

        self.TRIP = 0b10101010
        self.NORMAL = 0b01010101
        self.FAULT = 0b11001100
        self.ACK = 0b00110011
        self.WAKE = 0b10011001
        self.SLEEP = 0b01100110
        self.POWERSAVE = 0b01000100
        self.DETACH_USB = 0x43
        self.ATTACH_USB = 0x42
        self.RESET_PROBE = 0x47
        self.CLEAR_PROBE_COMMAND = 0x00
        #todo create a dictionary for looking up probe statuses.

class IrDA_Probe_I2C():
    """
    read and write commands to the lights
    """
    def __init__(self, I2CAddress, BusAddress = 2,):
        """#Set up Names and Registers"""
        self.COMMANDS = Probe_COMMANDS()
        self.registers(I2CAddress,BusAddress)
        self.READ_DELAY = 1
        #Setup I2C
        try:
            from smbus import SMBus
            self.i2cLib = "SMBUS"
            self.i2c = SMBus(self.BusAddress)
        except:
            print("SMBUS Not Found")

    def registers(self,I2CAddress,BusAddress):
        """sets all the registers and Variables used for communication"""
        self.I2CAddress = I2CAddress
        self.BusAddress = BusAddress

        self.BATTERY = 0
        self.COMMAND = 0
        self.SLEEP = 0

        self.COMMAND_REG    = 0x00
        self.BATTERY_REG    = 0x01
        self.STATUS_REG     = 0x02
        self.SLEEP_REG      = 0x03
    

    def read(self,address):
        """Wraper function for reading a byte of data from an address"""
        time.sleep(self.READ_DELAY)
        val = self.i2c.read_byte_data(self.I2CAddress, address)
        return val

    def write(self,address,data):
        """Wraper function for writing a byte to an address"""
        time.sleep(self.READ_DELAY)
        val = self.i2c.write_byte_data(self.I2CAddress, address, data)
        return val
    def writeBlock(self,address,l:list):
        """Wraper function for writing a block of data to an address"""
        time.sleep(self.READ_DELAY)
        val = self.i2c.write_i2c_block_data(self.I2CAddress, address, l)
        return val
    
    def readBattery(self):
        """Reads the battery status and returns that value - the battery status is also stored in self.BATTERY"""
        self.BATTERY = self.read(self.BATTERY_REG)
        return self.BATTERY
    
    def readStatus(self):
        """Reads the status register and returns that value - the command status is also stored in self.COMMAND"""
        self.STATUS = self.read(self.STATUS_REG)
        return self.STATUS
    
    def readSleep(self):
        """Reads the status register and returns that value - the command status is also stored in self.COMMAND"""
        self.SLEEP = self.read(self.SLEEP_REG)
        return self.SLEEP
    
    def readCommand(self):
        """Reads the command status and returns that value - the command status is also stored in self.COMMAND"""
        self.COMMAND = self.read(self.COMMAND_REG)
        return self.COMMAND
    
    def writeCommand(self,cmd):
        """writes the command status reads it and returns that value - the command status is also stored in self.COMMAND"""
        self.write(self.COMMAND_REG,cmd)
        self.COMMAND = self.read(self.COMMAND_REG)
        return self.COMMAND
    
    def wake(self):
        """Sends Wake Up Command to Probe Interface"""
        self.write(self.SLEEP_REG,self.COMMANDS.WAKE)

    def sleep(self):
        """Sends Sleep Command to Probe Interface"""
        self.write(self.SLEEP_REG,self.COMMANDS.SLEEP)
        
    def detachUSB(self):
        """Sends detach USB Command to Probe Interface"""
        self.write(self.SLEEP_REG,self.COMMANDS.DETACH_USB)
    def attachUSB(self):
        """Sends Sleep Command to Probe Interface"""
        self.write(self.SLEEP_REG,self.COMMANDS.ATTACH_USB)
    def resetProbe(self):
        """sends reset Command to the Probe"""
        self.write(self.SLEEP_REG,self.COMMANDS.RESET_PROBE)
    def clearCommands(self):
        """sends reset Command to the Probe"""
        self.write(self.SLEEP_REG,self.COMMANDS.CLEAR_PROBE_COMMAND)

    def updateStatus(self):
        self.readBattery()
        self.readCommand()
        self.readStatus()
        self.readSleep()



def testSleepMode(probe:IrDA_Probe_I2C):
    """Test the Probe Sleep Mode Command"""
    print("Testing Module....")
    time.sleep(0.01)
    #probe.updateStatus()
    #print("Status: {}\nBattery: {}\nCommand: {}\nSleep: {}".format(probe.STATUS, probe.BATTERY, probe.COMMAND, probe.SLEEP))
    #probe.sleep()
    #time.sleep(1)
    probe.updateStatus()
    print("Status: {}\nBattery: {}\nCommand: {}\nSleep: {}".format(probe.STATUS, probe.BATTERY, probe.COMMAND, probe.SLEEP))
    time.sleep(0.01)
    print("Sleep Command Sent...")
    probe.sleep()
    time.sleep(10)
    probe.wake()
    print("wake Command Sent...")

if( __name__ == "__main__"):
    import argparse
    #see https://docs.python.org/3/library/argparse.html# for documentation on the argparse module.
    parser = argparse.ArgumentParser(
        prog='IrDA Probe I2C',
        description='This is a Python I2C module for interacting with the Solo IrDA Probe Reciever',
        epilog='© Penta Machine Co. 2023')
    parser.add_argument("-t","--test",
                        action='store_true',
                        help="test the Sleep command - also reads the probe status and battery status from the receiver.")
    parser.add_argument("-s","--sleep",
                        action='store_true',
                        help="Command the probe to sleep.")
    parser.add_argument("-w","--wake",
                        action='store_true',
                        help="Command the probe to wake up.")
    parser.add_argument("-a","--attach",
                        action='store_true',
                        help="Command the probe to attach USB (for Programming).")
    parser.add_argument("-d","--detach",
                        action='store_true',
                        help="Command the probe to detach USB (for Programming).")
    parser.add_argument("-r","--reset",
                        action='store_true',
                        help="Command the probe reset.")
    parser.add_argument("-c","--clear",
                        action='store_true',
                        help="Clear any probe commands on the receiver.")
    parser.add_argument("--read",
                        action='store_true',
                        help="Read the Probe Status registers.")
    arg = parser.parse_args()
    #connect the probe
    probe = IrDA_Probe_I2C(I2CAddress = 0x44, BusAddress = 2)

    if arg.test:
        testSleepMode(probe)
    if arg.sleep:
        probe.sleep()
    if arg.wake:
        probe.wake()
    if arg.attach:
        probe.attachUSB()
    if arg.detach:
        probe.detachUSB()
    if arg.reset:
        probe.resetProbe()
    if arg.clear:
        probe.clearCommands()
    if arg.read:
        probe.updateStatus()
        print("Status: {}\nBattery: {}\nCommand: {}\nSleep: {}".format(probe.STATUS, probe.BATTERY, probe.COMMAND, probe.SLEEP))



