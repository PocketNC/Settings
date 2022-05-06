import metrology
import probe

# TODO - Take into account units, leaving the metrology and probe modules units agnostic.
#      - The metrology and probe modules don't really need to know about units, but in G
#      - code you are dealing with either mm (G21) or inches (G20). We should probably 
#      - convert to machine units (whatever is set in [TRAJ]LINEAR_UNITS) from whatever
#      - the current mode is (mm when in G21 or inches when in G20). 
#      - We should do this conversion in oword.py and namedparams.py when point data
#      - is stored or requested by the user. This comment is duplicated in oword.py and namedparams.py.
#      - See SOFT-846.

def add_point(self, x=0, y=0, z=0):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.addPoint(x,y,z)

def clear_points(self):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.clearPoints()

# Used for allocating a new feature set to avoid stomping on data from
# other contexts. In a given routine that is using feature numbers,
# start the routine with "o<push_feature_set> call" and end it with
# "o<pop_feature_set> call" and the routine will have free reign to modify
# any feature without stomping on other's data
def push_feature_set(self):
  manager = metrology.FeatureManager.getInstance()
  manager.push()

def pop_feature_set(self):
  manager = metrology.FeatureManager.getInstance()
  manager.pop()

def set_active_feature(self, id):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  featureSet.setActiveFeatureID(id)

def set_probe_direction(self, dirx, diry, dirz):
  cal = probe.getInstance()
  comp = cal.setProbeDirection(dirx, diry, dirz)

def disable_probe_calibration(self):
  cal = probe.getInstance()
  cal.disableCompensation()

def enable_probe_calibration(self):
  cal = probe.getInstance()
  cal.enableCompensation()

def set_probe_calibration_circle2d(self, actualDiameter, probeTipDiameter):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  cal = probe.getInstance()

  cal.setProbeCompensationCircle2D(actualDiameter, probeTipDiameter, feature)

def save_probe_calibration(self):
  cal = probe.getInstance()
  cal.saveProbeCompensation()
