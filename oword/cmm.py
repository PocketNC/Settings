from metrology import Feature
from cmmmanager import Cmm
import asyncio
from ipp import float3, readPointData
import ipp_routines as routines
from oword.penta import add_point

async def cmm_connect(self):
  cmm = Cmm.getInstance()

  if cmm.is_connected():
    return

  await cmm.connect()
  await cmm.EndSession().complete()
  await cmm.StartSession().complete()

async def cmm_disconnect(self):
  cmm = Cmm.getInstance()

  if cmm.is_connected():
    await cmm.EndSession().send()
    await cmm.disconnect()

async def cmm_go_to_clearance_y(self, y=250):
  cmm = Cmm.getInstance()

  await cmm.v2routines.go_to_clearance_y(y)

async def cmm_go_to_clearance_x(self, x=-250):
  cmm = Cmm.getInstance()

  await cmm.v2routines.go_to_clearance_x(x)

def cmm_set_skip_cmm(self, val):
  cmm = Cmm.getInstance()
  tf = abs(val) > 1e-6
  cmm.set_skip_cmm(tf)

async def cmm_set_part_csy(self,csy):
  cmm = Cmm.getInstance()

  cmm.routines.set_part_csy(csy)

async def cmm_move_relative(self, x, y, z):
  cmm = Cmm.getInstance()

  getCurrPosCmd = await cmm.Get("X(),Y(),Z()").data()
  startPos = readPointData(getCurrPosCmd.data_list[0])

  await cmm.GoTo((startPos + float3(x,y,z)).ToXYZString()).complete()

async def cmm_probe_sphere_relative(self, radius):
  cmm = Cmm.getInstance()

  pts = cmm.routines.probe_sphere_relative(radius)
  for pt in pts:
    add_point(self, pt.x, pt.y, pt.z)


def cmm_set_skip_updates(self, val):
  tf = abs(val) > 1e-6
  #calib.CalibManager.getInstance().set_config("skip_updates", tf)
