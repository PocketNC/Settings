import serial
import time
serial_out = serial.Serial('/dev/ttyACM0')
serial_in = serial.Serial('/dev/ttyACM1')

try:
    print("Listening for events")
    while True:
        for event in serial_in.read(8):
            # msg = event.strip()
            # message_parser(msg)
            time.sleep(0.01)
            print(event)

except KeyboardInterrupt:
    print("CTRL+C Caught")
    raise SystemExit
