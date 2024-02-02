import linuxcnc

c = linuxcnc.command()
s = linuxcnc.stat()
s.poll()

# 2.5 inches/second = 150 inches/minute
if s.max_velocity > 2.5:
  c.maxvel(2.5)

defaultRapidRate = 150/590

if s.rapidrate > defaultRapidRate:
  c.rapidrate(defaultRapidRate)
