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
        self.RESET_PROBE = 0x47
        self.SETBEEPCOMMAND = 0x45
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
        self.notes()
        self.READ_DELAY = 1
        #Setup I2C
        try:
            from smbus import SMBus
            self.i2cLib = "SMBUS"
            self.i2c = SMBus(self.BusAddress)
        except:
            print("SMBUS Not Found")
    def notes(self):
        """creates a dictionary of Notes for reference
        This list was found here https://pages.mtu.edu/~suits/notefreqs.html
        """
        self.Notes = {
            'C0':	16.35	,
            'CsDb0':	17.32	,
            'D0':	18.35	,
            'DsEb0':	19.45	,
            'E0':	20.6	,
            'F0':	21.83	,
            'FsGb0':	23.12	,
            'G0':	24.5	,
            'GsAb0':	25.96	,
            'A0':	27.5	,
            'AsBb0':	29.14	,
            'B0':	30.87	,
            'C1':	32.7	,
            'CsDb1':	34.65	,
            'D1':	36.71	,
            'DsEb1':	38.89	,
            'E1':	41.2	,
            'F1':	43.65	,
            'FsGb1':	46.25	,
            'G1':	49	,
            'GsAb1':	51.91	,
            'A1':	55	,
            'AsBb1':	58.27	,
            'B1':	61.74	,
            'C2':	65.41	,
            'CsDb2':	69.3	,
            'D2':	73.42	,
            'DsEb2':	77.78	,
            'E2':	82.41	,
            'F2':	87.31	,
            'FsGb2':	92.5	,
            'G2':	98	,
            'GsAb2':	103.83	,
            'A2':	110	,
            'AsBb2':	116.54	,
            'B2':	123.47	,
            'C3':	130.81	,
            'CsDb3':	138.59	,
            'D3':	146.83	,
            'DsEb3':	155.56	,
            'E3':	164.81	,
            'F3':	174.61	,
            'FsGb3':	185	,
            'G3':	196	,
            'GsAb3':	207.65	,
            'A3':	220	,
            'AsBb3':	233.08	,
            'B3':	246.94	,
            'C4':	261.63	,
            'CsDb4':	277.18	,
            'D4':	293.66	,
            'DsEb4':	311.13	,
            'E4':	329.63	,
            'F4':	349.23	,
            'FsGb4':	369.99	,
            'G4':	392	,
            'GsAb4':	415.3	,
            'A4':	440	,
            'AsBb4':	466.16	,
            'B4':	493.88	,
            'C5':	523.25	,
            'CsDb5':	554.37	,
            'D5':	587.33	,
            'DsEb5':	622.25	,
            'E5':	659.25	,
            'F5':	698.46	,
            'FsGb5':	739.99	,
            'G5':	783.99	,
            'GsAb5':	830.61	,
            'A5':	880	,
            'AsBb5':	932.33	,
            'B5':	987.77	,
            'C6':	1046.5	,
            'CsDb6':	1108.73	,
            'D6':	1174.66	,
            'DsEb6':	1244.51	,
            'E6':	1318.51	,
            'F6':	1396.91	,
            'FsGb6':	1479.98	,
            'G6':	1567.98	,
            'GsAb6':	1661.22	,
            'A6':	1760	,
            'AsBb6':	1864.66	,
            'B6':	1975.53	,
            'C7':	2093	,
            'CsDb7':	2217.46	,
            'D7':	2349.32	,
            'DsEb7':	2489.02	,
            'E7':	2637.02	,
            'F7':	2793.83	,
            'FsGb7':	2959.96	,
            'G7':	3135.96	,
            'GsAb7':	3322.44	,
            'A7':	3520	,
            'AsBb7':	3729.31	,
            'B7':	3951.07	,
            'C8':	4186.01	,
            'CsDb8':	4434.92	,
            'D8':	4698.63	,
            'DsEb8':	4978.03	,
            'E8':	5274.04	,
            'F8':	5587.65	,
            'FsGb8':	5919.91	,
            'G8':	6271.93	,
            'GsAb8':	6644.88	,
            'A8':	7040	,
            'AsBb8':	7458.62	,
            'B8':	7902.13	,
        }
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
        self.I2C_CMD_REG      = 0x03
        self.SLEEP_TIMEOUT_REG = 0x04
        self.BEEP_REG       = 0x05
        self.PER2_REG       = 0x06
        self.PER1_REG       = 0x07
        self.PER0_REG       = 0x08
        self.CCA2_REG       = 0x09
        self.CCA1_REG       = 0x0A
        self.CCA0_REG       = 0x0B
        self.CCB2_REG       = 0x0C
        self.CCB1_REG       = 0x0D
        self.CCB0_REG       = 0x0E

    def setBeep(self,frequency:float, duty_cycle:float):
        """set the frequency and duty_cycle for the beep"""
        clock = 24000000
        #print(frequency)
        #print(type(frequency))
        PER = int(clock/float(frequency))
        CCA = int(PER*duty_cycle)
        CCB = CCA
        if(frequency > clock/2):
            raise ValueError("Frequency {} is not allowed use a frequency > 0.5x the clock frequency({})".format(frequency,clock))
        elif( (CCA > 0xFFFFFF) | (CCB > 0xFFFFFF) ):
            raise ValueError("CCA {} or CCB {} register is out of range make sure you are using a valid duty_cycle (0.50 for 50%)!".format(CCA,CCB))
        #print("Frequency: {}\r\nCCA: {}\r\nCCB: {}".format(PER,CCA,CCB))
        new = [
            (PER >> 16)&0xFF,
            (PER >> 8)&0xFF,
            (PER >> 0)&0xFF,
            (CCA >> 16)&0xFF,
            (CCA >> 8)&0xFF,
            (CCA >> 0)&0xFF,
            (CCB >> 16)&0xFF,
            (CCB >> 8)&0xFF,
            (CCB >> 0)&0xFF
        ]
        #write all the Waveform Registers
        self.writeBlock(self.PER2_REG,new)
        #send a command to process the new values.
        self.write(self.I2C_CMD_REG, self.COMMANDS.SETBEEPCOMMAND)
    

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
        self.SLEEP = self.read(self.I2C_CMD_REG)
        return self.SLEEP
    
    def readCommand(self):
        """Reads the command status and returns that value - the command status is also stored in self.COMMAND"""
        self.COMMAND = self.read(self.COMMAND_REG)
        return self.COMMAND
    def readBeep(self):
        """read the beep status"""
        self.BEEP = self.read(self.BEEP_REG)
        return self.BEEP
    
    def writeCommand(self,cmd):
        """writes the command status reads it and returns that value - the command status is also stored in self.COMMAND"""
        self.write(self.COMMAND_REG,cmd)
        self.COMMAND = self.read(self.COMMAND_REG)
        return self.COMMAND
    
    def wake(self):
        """Sends Wake Up Command to Probe Interface"""
        self.write(self.I2C_CMD_REG,self.COMMANDS.WAKE)

    def sleep(self):
        """Sends Sleep Command to Probe Interface"""
        self.write(self.I2C_CMD_REG,self.COMMANDS.SLEEP)
        
    def resetProbe(self):
        """sends reset Command to the Probe"""
        self.write(self.I2C_CMD_REG,self.COMMANDS.RESET_PROBE)
    def clearCommands(self):
        """sends reset Command to the Probe"""
        self.write(self.I2C_CMD_REG,self.COMMANDS.CLEAR_PROBE_COMMAND)
    def beepOFF(self):
        """sends beep off command"""
        self.write(self.BEEP_REG,0)
    def beepON(self):
        """sends beep off command"""
        self.write(self.BEEP_REG,1)

    def updateStatus(self):
        self.readBattery()
        self.readCommand()
        self.readStatus()
        self.readSleep()
        self.readBeep()



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
    parser.add_argument("-r","--reset",
                        action='store_true',
                        help="Command the probe reset.")
    parser.add_argument("-c","--clear",
                        action='store_true',
                        help="Clear any probe commands on the receiver.")
    parser.add_argument("--beepON",
                        action='store_true',
                        help="Turn on the Beeper.")
    parser.add_argument("--beepOFF",
                        action='store_true',
                        help="Turn off the Beeper.")
    parser.add_argument("--read",
                        action='store_true',
                        help="Read the Probe Status registers.")
    

    subparsers = parser.add_subparsers(dest='subparser_name',help="sub-command help")

    ###SECTION FOR settime COMMAND
    parser_setTime = subparsers.add_parser("note", help="Set the Note - Note there are no hard limits set Some frequencies will not performe as well as others.")
    parser_setTime.add_argument("frequency",type=float,help="frequency in Hz")
    parser_setTime.add_argument("duty_cycle",type=float,help="duty cycle in decimal example 50 percent is 0.5")

    arg = parser.parse_args()
    #connect the probe
    probe = IrDA_Probe_I2C(I2CAddress = 0x44, BusAddress = 2)

    if arg.test:
        testSleepMode(probe)
    elif arg.beepOFF:
        probe.beepOFF()
    elif arg.beepON:
        probe.beepON()
    elif arg.sleep:
        probe.sleep()
    elif arg.wake:
        probe.wake()
    elif arg.reset:
        probe.resetProbe()
    elif arg.clear:
        probe.clearCommands()
    elif arg.read:
        probe.updateStatus()
        print("Status: {}\nBattery: {}\nCommand: {}\nSleep: {}\nBeep: {}".format(probe.STATUS, probe.BATTERY, probe.COMMAND, probe.SLEEP, probe.BEEP))
    elif (arg.subparser_name=="note"):
        print(arg)
        print(arg.subparser_name)
        probe.setBeep(arg.frequency,arg.duty_cycle)
    else:
        parser.print_help()




