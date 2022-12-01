import metrology
import probe
import math
import numpy
import importlib

import asyncio
import sys
import ipp_tests
import calib


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

def set_feature_transform_with_axis_angle(self, x, y, z, angle):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  feature.setTransformWithAxisAngle([x,y,z], math.radians(angle))

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

def project_points_onto_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  pointsFeature = featureSet.getFeature(pointsId)
  planeFeature = featureSet.getFeature(planeId)
  newFeature = featureSet.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)
    newFeature.addPoint(pointOnPlane[0], pointOnPlane[1], pointOnPlane[2])

def point_deviations_from_plane(self, pointsId, planeId, newId):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  pointsFeature = featureSet.getFeature(pointsId)
  planeFeature = featureSet.getFeature(planeId)
  newFeature = featureSet.getFeature(newId)

  newFeature.clearPoints()
  plane = planeFeature.plane()
  points = pointsFeature.points()

  for p in points:
    pointOnPlane = metrology.projectPointOntoPlane(p, plane)

    print("point: (%s, %s, %s)" % (p[0], p[1], p[2]))
    print("point on plane: (%s, %s, %s)" % (pointOnPlane[0], pointOnPlane[1], pointOnPlane[2]))

    dx = p[0]-pointOnPlane[0]
    dy = p[1]-pointOnPlane[1]
    dz = p[2]-pointOnPlane[2]
    print("mag: (%s)" % (math.sqrt(dx*dx+dy*dy+dz*dz),))

    newFeature.addPoint(dx,dy,dz)

def set_probe_calibration(self, actualDiameter, probeTipDiameter, rings, samplesPerRing, theta):
  manager = metrology.FeatureManager.getInstance()
  featureSet = manager.getActiveFeatureSet()
  feature = featureSet.getActiveFeature()
  cal = probe.getInstance()

  cal.setProbeCalibration(actualDiameter, probeTipDiameter, feature, rings, samplesPerRing, theta)

def save_probe_calibration(self):
  cal = probe.getInstance()
  cal.saveProbeCalibration()

def cmm_connect(self):
  try:
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().connect_to_cmm())
  except Exception as e:
    print(e)
    return str(e)

def cmm_disconnect(self):
  try:
    cm = calib.CalibManager.getInstance()
    if cm.client and cm.client.stream:
      asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().disconnect_from_cmm())
  except Exception as e:
    print(e)
    return str(e)

def cmm_setup(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CMM)
  except Exception as e:
    print(e)
    return str(e)

def cmm_go_to_clearance_y(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Y)
  except Exception as e:
    print(e)
    return str(e)

def cmm_go_to_clearance_z(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.GO_TO_CLEARANCE_Z)
  except Exception as e:
    print(e)
    return str(e)

def cmm_set_skip_cmm(self, val):
  try:
    tf = abs(val) > 1e-6
    calib.CalibManager.getInstance().set_state('skip_cmm', tf)
  except Exception as e:
    print(e)
    return str(e)

def cmm_set_skip_updates(self, val):
  try:
    tf = abs(val) > 1e-6
    calib.CalibManager.getInstance().set_config("skip_updates", tf)
  except Exception as e:
    print(e)
    return str(e)

def cmm_move_relative(self, x, y, z):
  try:
    print('cmm_move_relative oword')
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().move_relative(x,y,z))

  except Exception as e:
    print(e)
    return str(e)

def cmm_probe_sphere_relative(self, radius):
  try:
    print('cmm_probe_sphere_relative oword')
    asyncio.get_event_loop().run_until_complete(calib.CalibManager.getInstance().probe_sphere_relative(radius))

  except Exception as e:
    print(e)
    return str(e)

def v2_calib_connect(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CONNECT_TO_CMM)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_disconnect(self):
  try:
    cm = calib.CalibManager.getInstance()
    if cm.client and cm.client.stream:
      cm.run_step(calib.Steps.DISCONNECT_FROM_CMM)
  except Exception as e:
    return str(e)


def v2_calib_probe_machine_pos(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_MACHINE_POS)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_setup_part_csy(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_PART_CSY)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_spindle_pos(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_POS, x_nominal, z_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_spindle_at_tool_probe(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_AT_TOOL_PROBE)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_fixture_ball_pos(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_BALL_POS, y_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_fixture_plane_a90(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_PLANE_A90, y_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_tool_probe_offset(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.TOOL_PROBE_OFFSET)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_setup_cnc_csy(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CNC_CSY)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_top_plane(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_TOP_PLANE, y_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_home_offset_y(self, y, a, b):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_Y, y, a, b)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_home_offset_x(self, y, a, b):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_X, y, a, b)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_x(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X, x_nominal, z_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_x_home(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X_HOME, x_nominal, z_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_x_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_X_HOME)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_y(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y, y_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_y_home(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y_HOME, y_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_y_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_Y_HOME)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_z(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Z, x_nominal, z_nominal)
  except Exception as e:
    return str(e)

def v2_calib_probe_z_home(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Z_HOME, x_nominal, z_nominal)
  except Exception as e:
    return str(e)

def v2_calib_verify_z_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_Z_HOME)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_find_pos_fixture_rel_y_perp(self, y, a, b):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_Y_PERP, y, a, b)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_find_pos_fixture_rel_x_perp(self, y, a, b):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_X_PERP, y, a, b)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_find_pos_a(self, y_nominal, a_nominal):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_A, y_nominal, a_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_find_pos_b(self, y_nominal, b_nominal):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_B, y_nominal, b_nominal)
    print('probe_b return is %s' % r)
    return r
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_a(self, y_nominal, a_nominal):
  try:
    feat_name = "probe_a_%+.6f" % a_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_probe_a(self, y_nominal, a_nominal):
  try:
    feat_name = "verify_a_%+.6f" % a_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_a_home(self, y_nominal, a_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A_HOME, y_nominal, a_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_a_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOME)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_a_homing(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOMING)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_b(self, y_nominal, b_nominal):
  try:
    feat_name = "probe_b_%+.6f" % b_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_probe_b_home(self, y_nominal, b_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B_HOME, y_nominal, b_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_b_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOME)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_b_homing(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOMING)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_verify_probe_b(self, y_nominal, b_nominal):
  try:
    feat_name = "verify_b_%+.6f" % b_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_write_results(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_RESULTS)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_calc_calib(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CALC_CALIB)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_write_calib(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_CALIB)
  except Exception as e:
    return str(e)

def v2_calib_setup_verify(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_VERIFY)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_calc_verify(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CALC_VERIFY)
  except Exception as e:
    print(e)
    return str(e)

def v2_calib_write_verify(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_VERIFY)
  except Exception as e:
    return str(e)

def v2_calib_save(self):
  try:
    print('v2_calib_save')
    cm = calib.CalibManager.getInstance()
    cm.save_features()
  except Exception as e:
    return str(e)

def v2_calib_load(self):
  try:
    print('v2_calib_load')
    cm = calib.CalibManager.getInstance()
    cm.load_features()
  except Exception as e:
    return str(e)

def v2_calib_save_stage_probe_machine_pos(self):
  try:
    print('v2_calib_save_stage_probe_machine_pos')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_MACHINE_POS)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_probe_spindle_pos(self):
  try:
    print('v2_calib_save_stage_probe_spindle_pos')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_x(self):
  try:
    print('v2_calib_save_stage_characterize_x')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_X)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_y(self):
  try:
    print('v2_calib_save_stage_characterize_y')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Y)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_z(self):
  try:
    print('v2_calib_save_stage_characterize_z')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Z)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_a(self):
  try:
    print('v2_calib_save_stage_characterize_a')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_A)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_b(self):
  try:
    print('v2_calib_save_stage_characterize_b')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_machine_pos(self):
  try:
    print('v2_calib_load_stage_probe_machine_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_MACHINE_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_spindle_pos(self):
  try:
    print('v2_calib_load_stage_probe_spindle_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_fixture_ball_pos(self):
  try:
    print('v2_calib_load_stage_probe_fixture_ball_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_FIXTURE_BALL_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_top_plane(self):
  try:
    print('v2_calib_load_stage_probe_top_plane')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_TOP_PLANE)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_x(self):
  try:
    print('v2_calib_load_stage_homing_x')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_X)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_y(self):
  try:
    print('v2_calib_load_stage_homing_y')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Y)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_z(self):
  try:
    print('v2_calib_load_stage_homing_z')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Z)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_a(self):
  try:
    print('v2_calib_load_stage_homing_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_b(self):
  try:
    print('v2_calib_load_stage_homing_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_x(self):
  try:
    print('v2_calib_load_stage_characterize_x')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_X)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_y(self):
  try:
    print('v2_calib_load_stage_characterize_y')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Y)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_z(self):
  try:
    print('v2_calib_load_stage_characterize_z')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Z)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_a(self):
  try:
    print('v2_calib_load_stage_characterize_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_b(self):
  try:
    print('v2_calib_load_stage_characterize_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_tool_probe_offset(self):
  try:
    print('v2_calib_load_stage_tool_probe_offset')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.TOOL_PROBE_OFFSET)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_verify_a(self):
  try:
    print('v2_calib_load_stage_verify_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_verify_b(self):
  try:
    print('v2_calib_load_stage_verify_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_B)
  except Exception as e:
    return str(e)

def v2_calib_zmq_report(self):
  try:
    calib.CalibManager.getInstance().zmq_report()
  except Exception as e:
    print(e)
    return str(e)

def reload_calib(self):
  calib.reload()
  importlib.reload(ipp_tests)
  importlib.reload(calib)
