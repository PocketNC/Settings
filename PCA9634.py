#! /usr/bin/python3
# -*- coding: utf-8 -*-
import time
import binascii
# See datasheet https://www.mouser.com/datasheet/2/302/PCA9634-1127692.pdf p 10 for control registers.

class PCA9634():
    def __init__(self, address, bus=2):
        self.registers()
        self.address = address
        try:
            from smbus import SMBus
            self.smb = SMBus(bus)
        except:
            print("smbus not available. Please make sure this Module is installed.")
        
        val = self.smb.read_byte_data(self.address, 0x00)

    def LEDNames(self, LED0 = 0, LED1 = 0, LED2 = 0, LED3 = 0, LED4 = 0, LED5 = 0, LED6 = 0, LED7 = 0):
        #Sets a Dictionary of the LED Names
        self.Name = {LED0: 0, LED1: 1, LED2:2, LED3:3, LED4:4, LED5:5, LED6:6, LED7:7}

    def LEDRef(self, LED):
        if( type(LED) == type("") ):
            ret = self.Name[LED]
        else:
            ret = LED
        return ret

    def blinkConfig(self, dutyCycle, BPS):
        if(1 >= dutyCycle >=0 and 24 >= BPS >= 0.09375):
            #Set Duty Cycle
            GRPPWM = int(dutyCycle*256)
            self.smb.write_byte_data(self.address,self.GRPPWM, GRPPWM)
            #Set Blinks per second
            GFRQ = int( (24/BPS) -1 )
            self.smb.write_byte_data(self.address,self.GRPFREQ, GFRQ)
            return 1
        else:
            return 0

    def allOnFull(self):
        #                                                   0b76543210
        self.smb.write_byte_data(self.address,self.LEDOUT1, 0b01010101)
        self.smb.write_byte_data(self.address,self.LEDOUT0, 0b01010101)

    def allOnDim(self):
        #                                                   0b76543210
        self.smb.write_byte_data(self.address,self.LEDOUT1, 0b10101010)
        self.smb.write_byte_data(self.address,self.LEDOUT0, 0b10101010)

    def allBlink(self):
        #                                                   0b76543210
        self.smb.write_byte_data(self.address,self.LEDOUT1, 0b11111111)
        self.smb.write_byte_data(self.address,self.LEDOUT0, 0b11111111)

    def allOff(self):
        #                                                   0b76543210
        self.smb.write_byte_data(self.address,self.LEDOUT1, 0b00000000)
        self.smb.write_byte_data(self.address,self.LEDOUT0, 0b00000000)

    def LEDBlink(self,LEDAddr):
        #Get LED register and Mask
        tmp = self.LED_LIST[self.LEDRef(LEDAddr)]
        reg = tmp["REG"]
        mask = tmp["MASK"]
        shift = tmp["SHIFT"]
        #Get Current Register setting
        LEDSET = self.smb.read_byte_data(self.address, reg)
        #Change only the data needed
        LEDSET = LEDSET - (LEDSET & mask) +(self.LED_BLINK << shift)
        self.smb.write_byte_data(self.address,reg,LEDSET)

    def LEDOff(self, LEDAddr):
        #Get LED register and Mask
        tmp = self.LED_LIST[self.LEDRef(LEDAddr)]
        reg = tmp["REG"]
        mask = tmp["MASK"]
        shift = tmp["SHIFT"]
        #Get Current Register setting
        LEDSET = self.smb.read_byte_data(self.address, reg)
        #Change only the data needed
        LEDSET = LEDSET - (LEDSET & mask) +(self.LED_OFF << shift)
        self.smb.write_byte_data(self.address,reg,LEDSET)

    def LEDOn(self, LEDAddr):
        #Get LED register and Mask
        tmp = self.LED_LIST[self.LEDRef(LEDAddr)]
        reg = tmp["REG"]
        mask = tmp["MASK"]
        shift = tmp["SHIFT"]
        #Get Current Register setting
        LEDSET = self.smb.read_byte_data(self.address, reg)
        #Change only the data needed
        LEDSET = LEDSET - (LEDSET & mask) +(self.LED_ON << shift)
        self.smb.write_byte_data(self.address,reg,LEDSET)

    def LEDDim(self, LEDAddr, brightness = -1):
        #Get LED register and Mask
        tmp = self.LED_LIST[self.LEDRef(LEDAddr)]
        PWMreg = self.PWM_LIST[self.LEDRef(LEDAddr)]
        reg = tmp["REG"]
        mask = tmp["MASK"]
        shift = tmp["SHIFT"]
        #Get Current Register setting
        LEDSET = self.smb.read_byte_data(self.address, reg)
        #Change only the data needed
        LEDSET = LEDSET - (LEDSET & mask) +(self.LED_DIMM << shift)
        if(brightness < 0):
            brightness = self.smb.read_byte_data(self.address, PWMreg)
        self.setPWM( LEDAddr, brightness)
        # Turn LED to dimmed setting
        self.smb.write_byte_data(self.address,reg,LEDSET)

    def setPWM(self, LED, brightness=-1 ):
        reg = self.PWM_LIST[self.LEDRef(LED)]
        #if brightness valid set brightness
        if(0xFF >= brightness >= 0x00):
            self.smb.write_byte_data(self.address,reg, brightness)
            return 1
        else:
            return 0

    def soloConfig(self):
        #Minimal Settings to get a blinking Light.LED
        self.LEDNames(LED0 = "RED_E-STOP", LED1 = "GREEN_E-STOP", LED6 = "CYCLE_START", LED3 = "POWER_RED", LED4 = "POWER_GREEN", LED5 = "POWER_BLUE", LED2 = "FEED_HOLD", LED7 = "EMPTY")
        
        #General Configuration
        #                                                 0b76543210
        self.smb.write_byte_data(self.address,self.MODE1, 0b00000001)
        self.smb.write_byte_data(self.address,self.MODE2, 0b00100101)
        #invert and Totome Pole Enabled
        #otherwise Defaults
        #Set All pwm to 100%
        self.setPWM("RED_E-STOP", 0xFF)
        self.setPWM("GREEN_E-STOP", 0xFF)
        self.setPWM("CYCLE_START", 0xFF)
        self.setPWM("POWER_RED", 0xFF)
        self.setPWM("POWER_GREEN", 0xFF)
        self.setPWM("POWER_BLUE", 0xFF)
        self.setPWM("FEED_HOLD", 0xFF)
        self.setPWM("EMPTY", 0xFF)
        #Group Blink 
        self.blinkConfig(0.5, 1) #0.5 = 50% duty Cycle, 2 = 2blinks per second

    def demo(self):
        #                                                 0b76543210
        self.smb.write_byte_data(self.address,self.MODE1, 0b00000001)
        #Push Pull
        self.smb.write_byte_data(self.address,self.MODE2, 0b00100101)
        #invert and Totome Pole Enabled
        #otherwise Defaults
        #Blink
        duty = 0.5
        GRPPWM = int(duty*256)
        self.smb.write_byte_data(self.address,self.GRPPWM, GRPPWM)
        blinks = 0.5 #per second
        GFRQ = int((1/blinks)*24-1)
        print(GFRQ)
        self.smb.write_byte_data(self.address,self.GRPFREQ, GFRQ)

        #Set all pwm to 100%
        self.smb.write_byte_data(self.address,self.PWM0, 0xFF)
        self.smb.write_byte_data(self.address,self.PWM1, 0x00)
        self.smb.write_byte_data(self.address,self.PWM2, 0xFF)
        self.smb.write_byte_data(self.address,self.PWM3, 0xFF)
        self.smb.write_byte_data(self.address,self.PWM4, 0xFF)
        self.smb.write_byte_data(self.address,self.PWM5, 0xFF)
        self.smb.write_byte_data(self.address,self.PWM6, 0x0f)
        self.smb.write_byte_data(self.address,self.PWM7, 0xFF)

        #Toggle LED
        # LED1 on
        # LED 0 Red E-Stop
        # LED 1 Green E-Stop
        # LED 2 Cycle Start - Green
        # LED 3 Power LED -Red
        # LED 4 Power LED -Green
        # LED 5 Power LED -Blue
        # LED 6 Feed - Holde LED Red
        # LED 7 Extra
        # LED                                                 -3-2-1-0
        self.smb.write_byte_data(self.address,self.LEDOUT0, 0b11010011)
        # LED                                                 -7-6-5-4
        self.smb.write_byte_data(self.address,self.LEDOUT1, 0b00000101)

    def registers(self):
        self.MODE1 = 0x00
        self.MODE1_Key = {
            0:"ALLCALL", 
            1:"SUB3", 
            2:"SUB2",
            3:"SUB1", 
            4:"SLEEP", 
            5:"AI0", #Read Only
            6:"AI1", #Read Only
            7:"AI2"  #Read Only
            }
        self.MODE2 = 0x01
        self.MODE2_KEY = {
            0: "OUTNE0",
            1: "OUTNE1", 
            #00 = ~OE - 1 (output Drivers not enabled)LEDn = 0
            #01 = ~OE = 1 (Output Drivers not enabled) LEDn = 1 when OUTDRV = 1; LEDn = high-impedance when OUTDRV = 0 (same as OUTNE[1:0] = 10)
            #10 =  when OE = 1 (output drivers not enabled), LEDn = high-impedance
            #11 = Reserved
            2: "OURTDRV", #1 = Totem pole, 0 = open Drain
            3: "OCH", #0 = Change on Stop 1 = Change on Ack
            4: "INVRT", #0 Do not Invert 1 = Invert
            5: "DMBLINK", #Group Control 1 = Blink, 0 = dimming
            6: "READ_ONLY_1", #0
            7: "READ_ONLY_2" #0
        }
        self.PWMVAL = {"START": 0x00,"STOP": 0xFF}#duty = PWM/256, 0xFF = 100% on  0x00 = 0% on
        self.PWM_LIST = [ 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
        self.PWM0 = 0x02
        self.PWM1 = 0x03
        self.PWM2 = 0x04
        self.PWM3 = 0x05
        self.PWM4 = 0x06
        self.PWM5 = 0x07
        self.PWM6 = 0x08
        self.PWM7 = 0x09
        self.GRPPWM = 0x0A
        self.GRPFREQ = 0x0B
        #LED_STATUS Constants
        self.LED_ON = 0b01
        self.LED_BLINK = 0b11 #also group/individual dimming
        self.LED_OFF = 0b00
        self.LED_DIMM = 0b10
        self.LED_LIST = {
            #           0b76543210
            0: {"MASK": 0b00000011 , "REG": 0x0C, "SHIFT": 0},
            1: {"MASK": 0b00001100 , "REG": 0x0C, "SHIFT": 2},
            2: {"MASK": 0b00110000 , "REG": 0x0C, "SHIFT": 4},
            3: {"MASK": 0b11000000 , "REG": 0x0C, "SHIFT": 6},
            4: {"MASK": 0b00000011 , "REG": 0x0D, "SHIFT": 0},
            5: {"MASK": 0b00001100 , "REG": 0x0D, "SHIFT": 2},
            6: {"MASK": 0b00110000 , "REG": 0x0D, "SHIFT": 4},
            7: {"MASK": 0b11000000 , "REG": 0x0D, "SHIFT": 6},
            }
        self.LEDOUT0 = 0x0C
        self.LEDOUT1 = 0x0D
        self.SUBADR1 = 0x0E
        self.SUBADR2 = 0x0F
        self.SUBADR3 = 0x10
        self.ALLCALLADDR = 0x11

    def setMode1(self, AllCall =0, Port2 = 0, Port3 = 0, Port4 = 0, Port5 = 0, Port6 = 0, Port7 = 0):
        byte = AllCall + (Port1 << 1) + (Port2 << 2) + (Port3 << 3 ) + (Port4 << 4 ) + (Port5 << 5 ) + (Port6 << 6 ) + (Port7 << 7 )
        self.write(PORT_DISABLE_SELF,byte)
    def setMode2(self, AllCall =0, Port2 = 0, Port3 = 0, Port4 = 0, Port5 = 0, Port6 = 0, Port7 = 0):
        byte = AllCall + (Port1 << 1) + (Port2 << 2) + (Port3 << 3 ) + (Port4 << 4 ) + (Port5 << 5 ) + (Port6 << 6 ) + (Port7 << 7 )
        self.write(PORT_DISABLE_SELF,byte)


if( __name__ == "__main__"): 
    LED = PCA9634(0x73)
    print("PCA9634 Test")
    LED.soloConfig()
    print("LED Driver Configured")
    LED.allOnDim()
    print("All Dimmed")
    time.sleep(1)
    print("cycle start 50%")
    LED.LEDDim("CYCLE_START", int(0xff/2))
    time.sleep(1)
    print("All Blink")
    LED.allBlink()
    time.sleep(1)
    print("All off")
    LED.allOff()
    time.sleep(2)
    l = [ "FEED_HOLD", "POWER_BLUE", "POWER_GREEN", "POWER_RED", "CYCLE_START", "GREEN_E-STOP", "RED_E-STOP"]
    for x in l:
        print("{} ON".format(x) )
        LED.LEDOn(x)
        time.sleep(1)
        print("{} BLINK".format(x) )
        LED.LEDBlink(x)
        time.sleep(1)
        print("{} DIM".format(x) )
        LED.LEDDim(x)
        time.sleep(2)
        print("{} OFF".format(x) )
        LED.LEDOff(x)
        time.sleep(1)
