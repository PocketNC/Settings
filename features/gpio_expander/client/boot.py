# boot.py
import usb_cdc
import usb_hid
import usb_midi

usb_cdc.enable(console=True, data=True)
usb_hid.disable()
usb_midi.disable()
