"""
`owords` for interacting with a probe.
"""
import logging
import probe_calibration
import metrology
from scipy.spatial.transform import Rotation as R

logger = logging.getLogger(__name__)

def set_probe_direction(self, dirx, diry, dirz):
  cal = probe_calibration.getInstance()
  tcpc = self.params["_hal[motion.switchkins-type]"]
  if tcpc:
    # TODO - this is solo only, need to implement generic 
    # kinematics here SOFT-1114
    bWorkOffset = self.params[int(5225+20*(self.params[5220]-1))]
    cWorkOffset = self.params[int(5226+20*(self.params[5220]-1))]
    b = self.params["_b"]+bWorkOffset
    c = self.params["_c"]+cWorkOffset
    rotation = R.from_euler('zy', [c, b], degrees=True)
    rotatedDir = rotation.apply([ [dirx, diry, dirz] ])
    logger.debug(f"setting probe direction b{b} c{c}")
    logger.debug(f"local direction {dirx} {diry} {dirz}")
    logger.debug(f"global direction {rotatedDir[0][0]} {rotatedDir[0][1]} {rotatedDir[0][2]}")
    comp = cal.setProbeDirection(rotatedDir[0][0], rotatedDir[0][1], rotatedDir[0][2])
  else:
    comp = cal.setProbeDirection(dirx, diry, dirz)

def disable_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.disableCompensation()

def enable_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.enableCompensation()

def set_probe_calibration(self, actualDiameter, probeTipDiameter, rings, samplesPerRing, theta):
  manager = metrology.FeatureManager.getInstance()
  featureMap = manager.getActiveFeatureMap()
  feature = featureMap.getActiveFeature()
  cal = probe_calibration.getInstance()

  cal.setProbeCalibration(actualDiameter, probeTipDiameter, feature, int(rings), int(samplesPerRing), theta)

def save_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.saveProbeCalibration()

