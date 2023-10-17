import board
import time
import digitalio
import usb_cdc

# How long will do we sleep in between
#  loops
from settings import LOOP_TIMING

s = usb_cdc.data

p0 = digitalio.DigitalInOut(board.D0)
p2 = digitalio.DigitalInOut(board.D2)
p3 = digitalio.DigitalInOut(board.D3)
p4 = digitalio.DigitalInOut(board.D4)

p0.direction = digitalio.Direction.OUTPUT
p2.direction = digitalio.Direction.OUTPUT
p3.direction = digitalio.Direction.INPUT
p4.direction = digitalio.Direction.INPUT

p3.pull = digitalio.Pull.UP
p4.pull = digitalio.Pull.UP

def set_states(newval):
    newval = str(newval, 'ascii')

    # Direct indexing is faster than string matching
    p2.value = int(newval[4])
    p0.value = int(newval[5])

def poll_callback(previous_value):
    # Do we have any messages?
    while s.in_waiting:
        incoming = s.read(6)
        set_states(incoming)
        # We only care about the first 6 bytes
        break

    outval = 0b0000
    # False will evaulate to 0
    # Multiplying a True by the bitmask position
    # is computationally cheaper than a branching
    # operation
    outval = outval + int(p0.value) * 1
    outval = outval + int(p2.value) * 2
    outval = outval + int(p3.value) * 4
    outval = outval + int(p4.value) * 8

    if outval != previous_value:
        outstr = f"{int(outval):#06b}"
        outbin = bytes(outstr, 'ascii')
        s.write(outbin)
    return outval

if __name__ == '__main__':
    # Flush anything in the queue
    s.flush()
    val = 0b0000 # Initialize the previous value to 0
    while True:
        val = poll_callback(val)
        time.sleep(LOOP_TIMING)
