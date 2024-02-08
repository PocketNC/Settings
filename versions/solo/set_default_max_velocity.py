import linuxcnc
import ini
import os

POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
INI_FILE_CACHE = ini.read_ini_data(os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini"))

defaultMaxVelocityParam = ini.get_parameter(INI_FILE_CACHE, 'PENTA', 'DEFAULT_MAX_VELOCITY')
defaultMaxVelocity = float(defaultMaxVelocityParam['values']['value'] if defaultMaxVelocityParam else 3.33333)

c = linuxcnc.command()
s = linuxcnc.stat()
s.poll()

if s.max_velocity > defaultMaxVelocity:
  c.maxvel(defaultMaxVelocity)
