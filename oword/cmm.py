import calib
import asyncio

def cmm_connect(self):
  asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().connect_to_cmm())

async def cmm_disconnect(self):
  cm = calib.CalibManager.getInstance()
  if cm.client and cm.client.is_connected():
    await calib.CalibManager.getInstance().disconnect_from_cmm()

def cmm_setup(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CMM)

def cmm_go_to_clearance_y(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Y)

def cmm_go_to_clearance_z(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Z)

def cmm_set_skip_cmm(self, val):
  tf = abs(val) > 1e-6
  calib.CalibManager.getInstance().set_config('skip_cmm', tf)

def cmm_set_skip_updates(self, val):
  tf = abs(val) > 1e-6
  calib.CalibManager.getInstance().set_config("skip_updates", tf)

async def cmm_move_relative(self, x, y, z):
  await calib.CalibManager.getInstance().move_relative(x,y,z)

async def cmm_probe_sphere_relative(self, radius):
  await calib.CalibManager.getInstance().probe_sphere_relative(radius)

