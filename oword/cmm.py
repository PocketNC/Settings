import calib
import asyncio

def cmm_connect(self):
  try:
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().connect_to_cmm())
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_disconnect(self):
  try:
    cm = calib.CalibManager.getInstance()
    if cm.client and cm.client.is_connected():
      asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().disconnect_from_cmm())
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_setup(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CMM)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_go_to_clearance_y(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Y)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_go_to_clearance_z(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Z)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_set_skip_cmm(self, val):
  try:
    tf = abs(val) > 1e-6
    calib.CalibManager.getInstance().set_config('skip_cmm', tf)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_set_skip_updates(self, val):
  try:
    tf = abs(val) > 1e-6
    calib.CalibManager.getInstance().set_config("skip_updates", tf)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_move_relative(self, x, y, z):
  try:
    logger.debug('cmm_move_relative oword')
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().move_relative(x,y,z))

  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def cmm_probe_sphere_relative(self, radius):
  try:
    logger.debug('cmm_probe_sphere_relative oword')
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().probe_sphere_relative(radius))

  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

