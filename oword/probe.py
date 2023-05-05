"""
`owords` for interacting with a probe.
"""
import logging
import probe_calibration

logger = logging.getLogger(__name__)

def set_probe_direction(self, dirx, diry, dirz):
  cal = probe_calibration.getInstance()
  comp = cal.setProbeDirection(dirx, diry, dirz)

def disable_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.disableCompensation()

def enable_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.enableCompensation()

def set_probe_calibration(self, actualDiameter, probeTipDiameter, rings, samplesPerRing, theta):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  cal = probe_calibration.getInstance()

  cal.setProbeCalibration(actualDiameter, probeTipDiameter, feature, rings, samplesPerRing, theta)

def save_probe_calibration(self):
  cal = probe_calibration.getInstance()
  cal.saveProbeCalibration()

