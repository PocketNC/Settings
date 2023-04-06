#! /usr/bin/python3
# -*- coding: utf-8 -*-
import time
import binascii

#USB_Hub_Controll
class USB2507():
    #Read Write Functions For Backwards Compatibility
    def read(self,address):
        #print(self.address)
        #print(address)
        if self.i2cLib == "SMBUS":
            time.sleep(self.READ_DELAY)
            val = self.i2c.read_byte_data(self.address, address)
        else:
            val = self.i2c.readU8(address)
        return val
    def write(self,address,data):
        if self.i2cLib == "SMBUS":
            time.sleep(self.READ_DELAY)
            val = self.i2c.write_byte_data(self.address, address, data)
        else:
            val = self.i2c.write8(address,data)
        return val
    def Available(self):
        try:
            Status = self.i2c.read_byte_data(self.address, self.STATUS)
            return True, Status
        except:
            return False, False
    #Init Class
    def __init__(self, address, BusAddr = 2):
        self.BusAddr = BusAddr
        try:
            from smbus import SMBus
            self.i2cLib = "SMBUS"
        except:
            print("SMBUS Not Found")
            try:
                from Adafruit_GPIO.I2C import Device
                self.i2cLib = "Adafruit_GPIO.I2C"
            except: 
                print("Adafruit_GPIO.I2C Not Available")
                try:
                    from Adafruit_I2C import Adafruit_I2C
                    self.i2cLib = "Adafruit_I2C"
                except: 
                    print("Adafruit_I2C Not Available")
                    error = "init.. USB2507 not accessible at this address"+ hex(self.address)
                    raise NameError(error)
        self.defaults(address)
        if self.i2cLib == "SMBUS":
            self.i2c = SMBus(self.BusAddr)
            time.sleep(1)
        elif self.i2cLib == "Adafruit_GPIO.I2C":
            self.i2c = Device(self.address,self.BusAddr)
        elif self.i2cLib == "Adafruit_I2C":
            self.i2c = adafruit_I2C(self.address,self.BusAddr)
        else:
            print("I2C Buss Error....")
    def readStatus(self):
        val = self.read(self.STATUS)
        ret = dict()
        ret["7-3"] = "Reserved"
        ret["Reset"]         = val & 0b00000100
        ret["Write_Protect"] = val & 0b00000010
        ret["USB_Attach"]    = val & 0b00000001
        return ret
    #Read Product ID
    def readPID(self):
        LSB = self.read(self.PID_LSB)
        MSB = self.read(self.PID_MSB)
        ret = (MSB << 8) + LSB
        return(ret)
    #Read Product ID
    def writePID(self, LSB = False , MSB = False):
        if(LSB == False or MSB == False):
            LSB = 0x00
            MSB = 0x00
        self.write(self.PID_LSB, LSB)
        self.write(self.PID_MSB, MSB)

    #Read Device ID
    def readDID(self):
        LSB = self.read(self.DID_LSB)
        MSB = self.read(self.DID_MSB)
        ret = (MSB << 8) + LSB
        return(ret)
    #Write Device ID
    def writeDID(self, LSB = False , MSB = False):
        if(LSB == False or MSB == False):
            LSB = 0x00
            MSB = 0x00
        self.write(self.DID_LSB, LSB)
        self.write(self.DID_MSB, MSB)
    #Read Vendor ID
    def readVID(self):
        LSB = self.read(self.VID_LSB)
        MSB = self.read(self.VID_MSB)
        ret = (MSB << 8) + LSB
        return(ret)
    #Write Vendor ID
    def writeVID(self, LSB = False , MSB = False):
        if(LSB == False or MSB == False):
            LSB = 0x00
            MSB = 0x00
        self.write(self.VID_LSB, LSB)
        self.write(self.VID_MSB, MSB)

    def writeConfig(self, 
        SELF_BUS_PWR = 2, PORT_IND = 2, HS_DISABLE = 3, MTT_ENABLE = 4, 
        EOP_DISABLE = 2, CURRENT_SNS = 2, PORT_PWR = 2,
        DYNAMIC_POWER = 2, OC_TIMER = 4, COMPOUND = 2
    ):
        #Get Old Values
        Vals = self.readConfig()
        Config1 = Vals["Byte1"]
        Config2 = Vals["Byte2"]
        #Config 1 Changes
        if(SELF_BUS_PWR < 2):
            Config1 = self.SetBit(Config1, SELF_BUS_PWR,7)
        if(PORT_IND < 2):
            Config1 = self.SetBit(Config1, PORT_IND,6)
        if(HS_DISABLE < 2):
            Config1 = self.SetBit(Config1, HS_DISABLE,5)
        if(MTT_ENABLE < 2):
            Config1 = self.SetBit(Config1, MTT_ENABLE,4)
        if(EOP_DISABLE < 2):
            Config1 = self.SetBit(Config1, EOP_DISABLE,3)
        if(CURRENT_SNS < 2):
            Config1 = self.SetBit(Config1, CURRENT_SNS,1)
        if(PORT_PWR < 2):
            Config1 = self.SetBit(Config1, PORT_PWR,0)
        #Config 2 Changes
        if(DYNAMIC_POWER < 2):
            Config2 = self.SetBit(Config2, DYNAMIC_POWER, 7)
        if(OC_TIMER < 4):
            Config2 = self.SetBit(Config2, (OC_TIMER & 0b01), 5)
            Config2 = self.SetBit(Config2, (OC_TIMER & 0b10) >> 1 , 4)
        if(COMPOUND < 2):
            Config2 = self.SetBit(Config2, COMPOUND, 3)

        # Modify only Values with 1.
        self.write(self.CONFIG_DB_1,Config1)
        self.write(self.CONFIG_DB_2,Config2)
    #Helper Function to set a specific bit
    def SetBit(self, byte, bit, n):
        mask = 1 << n
        B = bit << n
        return ( byte-(mask&byte) + B )
    #ReadConfiguration
    def readConfig(self):
        Config1 = self.read(self.CONFIG_DB_1)
        Config2 = self.read(self.CONFIG_DB_2)
        #Parse
        ret = dict()
        #Config1                             0b76543210  >> x
        ret["Byte1"]            = Config1
        ret["Byte2"]            = Config2
        ret["SELF_BUS_PWR"]     = (Config1 & 0b10000000) >> 7
        ret["PORT_IND"]         = (Config1 & 0b01000000) >> 6
        ret["HS_DISABLE"]       = (Config1 & 0b00100000) >> 5
        ret["MTT_ENABLE"]       = (Config1 & 0b00010000) >> 4
        ret["EOP_DISABLE"]      = (Config1 & 0b00001000) >> 3
        ret["CURRENT_SNS"]      = (Config1 & 0b00000110) >> 1
        ret["CURRENT_SNS"] = {"BIN": ret["CURRENT_SNS"], "ASCII": self.CURRENT_SNS_B_A[ret["CURRENT_SNS"]]}
        ret["PORT_PWR"]         = (Config1 & 0b00000001)
        #config2
        ret["DYNAMIC_PWR"]      = (Config2 & 0b10000000) >> 7
        ret["RESERVED_C2_6"]    = (Config2 & 0b01000000) >> 6
        ret["OC_TIMER"]         = (Config2 & 0b00110000) >> 4
        ret["OC_TIMER"] = {"BIN": ret["OC_TIMER"], "ASCII": self.OC_TIMER_B_A[ret["OC_TIMER"]] }
        #00 = 0.1ms
        #01 = 2ms
        #10 = 4ms
        #11 = 6ms
        ret["Compound"]         = (Config2 & 0b00001000) >> 3
        ret["RESERVED_C2_2-0"]  = (Config2 & 0b00000111)
        return ret
    #Reset SMBUS
    def SMBReset(self):
        self.write(self.STATUS, 0x04)
    #Write Protect - set this bit to preveent accidental changes to USB Hub
    def WRITE_PROTECT(self):
        self.write(self.STATUS, 0x02)
    #Disables SMBUS interface and attaches to the upfacing port
    def USB_ATTACH(self):
        self.write(self.STATUS, 0x01)
    #Max Power drawn from host when bus powered
    def setMaxBusPower(self,power):
        if( 510 >= power >= 2):
            self.write(self.MAX_POWER_BUS, int(power/2))
        else:
            error = "Value {:0x} out of bounds".format(int(power/2))
            raise NameError(error)
    #Max Power drawn from host when self powered. A value of 50 (decimal) indicates 100mA.
    def setMaxSelfPower(self,power):
        if( 100 >= power >= 2):
            self.write(self.MAX_POWER_SELF, int(power/2))
        else:
            error = "Value {:0x} out of bounds".format(int(power/2) )
            raise NameError(error)
    #Max Current drawn from Host when bus powered
    def setMaxBusCurrent(self,power):
        if( 510 >= power >= 2):
            self.write(self.HUB_MAX_CURRENT_BUS, int(power/2) )
        else:
            error = "Value {:0x} out of bounds".format(int(power/2))
            raise NameError(error)
    #Max Current drawn from Host when self powered
    def setMaxSelfCurrent(self,power):#per datasheet this value should not be set above 100mA
        if( 100 >= power >= 2):
            self.write(self.HUB_MAX_CURRENT_SELF, int(power/2))
        else:
            error = "Value {:0x} out of bounds".format(int(power/2))
            raise NameError(error)
    #Time for Bus power to be good when enabled by the host.
    def setPowerOnTime(self,time):
        if( 510 >= time >= 2):
            self.write(self.POWER_ON_TIME, int(time/2))
        else:
            error = "Value {:0x} out of bounds".format(int(time/2))
            raise NameError(error)

    #Set Non Removable Devices
    def setNRDevices(self, Port1 =0, Port2 = 0, Port3 = 0, Port4 = 0, Port5 = 0, Port6 = 0, Port7 = 0):
        byte = 0 + (Port1 << 1) + (Port2 << 2) + (Port3 << 3 ) + (Port4 << 4 ) + (Port5 << 5 ) + (Port6 << 6 ) + (Port7 << 7 )
        self.write(NON_REMOVABLE_DEVICES,byte)
        
    #Disable Ports
    def setDisabledPortsSelf(self, Port1 =0, Port2 = 0, Port3 = 0, Port4 = 0, Port5 = 0, Port6 = 0, Port7 = 0):
        byte = 0 + (Port1 << 1) + (Port2 << 2) + (Port3 << 3 ) + (Port4 << 4 ) + (Port5 << 5 ) + (Port6 << 6 ) + (Port7 << 7 )
        self.write(PORT_DISABLE_SELF,byte)
    def setDisabledPortsBUS(self, Port1 =0, Port2 = 0, Port3 = 0, Port4 = 0, Port5 = 0, Port6 = 0, Port7 = 0):
        byte = 0 + (Port1 << 1) + (Port2 << 2) + (Port3 << 3 ) + (Port4 << 4 ) + (Port5 << 5 ) + (Port6 << 6 ) + (Port7 << 7 )
        self.write(PORT_DISABLE_BUS,byte)
    #Set Default Data
    def defaults(self, address):
        #Set Read Time Delay
        self.READ_DELAY = 0.1
        #Device Addres
        self.address = address
        #Device Register Addresses
        self.STATUS = 0x00
        #Vendor ID
        self.VID_LSB = 0x01
        self.VID_MSB = 0x02
        #Product ID
        self.PID_LSB = 0x03
        self.PID_MSB = 0x04
        #Device ID
        self.DID_LSB = 0x05
        self.DID_MSB = 0x06
        #Configuration
        self.CONFIG_DB_1 = 0x07
        #Config 1 Bits 1 and 2
        #00 = Ganged sensing (all ports together).
        #01 = Individual port-by-port
        self.CURRENT_SNS_B_A = { 0: "Ganged Sensing", 1: "Individual Sensing", 2: "BAD Value", 3: "BAD Value"}
        self.CONFIG_DB_2 = 0x08
        #Config 2 Bit 3
        #00 = 0.1ms
        #01 = 2ms
        #10 = 4ms
        #11 = 6ms
        self.OC_TIMER_B_A = { 0: "0.1ms", 1: "2ms", 2: "4ms", 3: "6ms"}
        #Non-Removable Device: Indicates which port(s) include non-removable devices. ‘0’ = port is removable, ‘1’ = port is non-removable.
        #BIT 0 always = 0
        self.NON_REMOVABLE_DEVICES = 0x09
        #Port Disable Self-Powered: Disables 1 or more contiguous ports. ‘0’ = port is available, ‘1’ = port is disabled.
        #BIT 0 always = 0
        self.PORT_DISABLE_SELF = 0x0A
        #Port Disable BUS-Powered: Disables 1 or more contiguous ports. ‘0’ = port is available, ‘1’ = port is disabled.
        #BIT 0 always = 0
        self.PORT_DISABLE_BUS = 0x0B
        #The Maximum Power a self powered Hub can consume from the Host.
        self.MAX_POWER_SELF = 0x0C
        #The Maximum Power a bus powered Hub can consume from the Host.
        self.MAX_POWER_BUS = 0x0D
        #The Maximum Current a self powered Hub can consume from the Host.
        self.HUB_MAX_CURRENT_SELF = 0x0E
        #The Maximum Current a Bus powerd Hub can consume from the host.
        self.HUB_MAX_CURRENT_BUS = 0x0F
        #Power On Time: The length of time that it takes (in 2 ms intervals) from the 
        # time the host initiated power-on sequence begins on a port until power is good
        # on that port.
        self.POWER_ON_TIME = 0x10


if( __name__ == "__main__"): 
    print("USB2507 Test")
    #1. Initialize the Class
    USB = USB2507(0x2C, BusAddr=2)
    #1 Check if USB Hub is accesible - If the Hub has already been configured and set up, the USB will not be usable by the SMBUS
    Readable, Status = USB.Available()
    print(Readable, Status)
    if( Readable ):
        print("USB Hub Is Available")
    else:
        print("USB Hub Not Available")
        exit()
    #use the default Vendor ID and Product ID from Microchip.(was owned by Standard Microsystems Corp.)
    print("Writing Device ID.")
    USB.writeDID(LSB = USB.address , MSB = 0x00)
    print("Writing Vendor ID.")
    USB.writeVID(LSB = 0x24 , MSB = 0x04)
    print("Writing Product ID.")
    USB.writePID(LSB = 0x07 , MSB = 0x25)
    #Demonstrate Reading Status, Vendor ID, Product ID, and Device ID
    # Vendor ID is issued by the USB IF(USB Implementers Forum INC) https://www.usb.org/about
    stat = USB.readStatus()
    print("status", stat)
    VID = USB.readVID()
    print("Vendor ID", VID)
    PID = USB.readPID()
    print("Product ID", PID)
    DID = USB.readDID()
    print("Device ID", DID)
    #3 Configure the USB - (Config bytes 1 and 2)
    USB.writeConfig(DYNAMIC_POWER = 0,SELF_BUS_PWR=1, PORT_IND = 1, CURRENT_SNS = 1, PORT_PWR = 1)
    print("USB Configured")
    #Reading the Configuration we could add a verification step
    config = USB.readConfig()
    print(config)
    #4. set Power And Current Limits
    # Set th time the host initiated power-on sequence begins on a port until power is good in ms
    USB.setPowerOnTime(10)
    #The Maximum Current a self powered Hub can consume from the Host
    USB.setMaxSelfCurrent(2)#per datasheet this value should not be set above 100mA
    #The Maximum Current a bus powered Hub can consume from the Host
    USB.setMaxBusCurrent(510)
    #The maximum power a self powerd Hub can consume from the Host
    USB.setMaxSelfPower(2)#per datasheet this value should not be set above 100mA

    #5. Write Protect
    USB.WRITE_PROTECT()
    #6. Command the Hub to attach
    USB.USB_ATTACH()
    
    pass
