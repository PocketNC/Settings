import linuxcnc


# Resetting the linuxcnc interpreter will cause status values to be refetched
# We are using this to workaround an issue where status items for work offset
# systems were erroneously always reported as 0 after startup, when behind
# the scenes the actual effective values are whatever was active at shutdown.
c = linuxcnc.command()
c.reset_interpreter()
