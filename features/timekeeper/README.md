timekeeper
==========

This feature is used to keep track of the total run time of the spindle. It reads/writes the time to
the EEPROM chip on the main board.

To facilitate testing, wear-leveling logic is separated from the HAL component file.

Tests are order dependent. Run with command:
  pythom -m unittest test
