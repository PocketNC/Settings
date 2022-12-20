import logging
from cmmmanager import Cmm
from ipp import Csy
import v2calculations
from calibstate import CalibState, Stages
from v2routines import V2_10, V2_50, PROBE_DIA, BEST_FIT_SPHERE_ERROR, SPINDLE_BALL_DIA_10, SPINDLE_BALL_DIA_50, APPROX_FIXTURE_BALL_HOME, FIXTURE_BALL_DIA
import numpy as np

logger = logging.getLogger(__name__)

class CalibException(Exception):
  pass


async def v2_calib_setup_cmm(self):
  """
  Sets up the basics so we can command the CMM:
  1) Clears all errors.
  2) Homes all axes.
  3) Loads the tool we use during the calibration routines.
  """
  cmm = Cmm.getInstance()
  CMM_SPEED = 500
  CMM_ACCEL = 450

  await cmm.ClearAllErrors().complete()
  await cmm.routines.ensure_homed()
  await cmm.routines.ensure_tool_loaded("Component_3.1.50.4.A0.0-B0.0")
  await cmm.SetProp("Tool.GoToPar.Speed(%s)" % CMM_SPEED).ack()
  await cmm.SetProp("Tool.GoToPar.Accel(%s)" % CMM_ACCEL).ack()

async def v2_calib_probe_machine_pos(self):
  """
  1) Sets up a Part CSY (coordinate system) for a specific
     slot (currently the front right slot). The
     origin is approximately the back right corner of the
     L-bracket on the V2. The +X direction of the Part CSY
     is oriented in the +Z direction of the V2. The +Y direction 
     of the Part CSY is aligned with the +X direction of the V2.
     The +Z direction of the Part CSY is aligned with the +Y 
     direction of the V2. 
  2) Probes the V2 to setup a Part CSY with the origin at the
     the back right corner of the L bracket with the X, Y and Z
     axes aligned roughly with the V2 (as closely as they can
     be without fully characterizing their motion).
  3) Retract to a safety clearance
  """
  cmm = Cmm.getInstance()

  # TODO - implement some kind of slot system so we can
  # have multiple machines on a single CMM. For now these
  # are setup for a machine in the front right of the CMM.

  APPROX_CSY_FRONT_RIGHT_SLOT = Csy(653.0, 134.0, 126.5, 0, -90, 0)
  await cmm.routines.set_part_csy(APPROX_CSY_FRONT_RIGHT_SLOT)

  (L_bracket_top_face, L_bracket_back_line, L_bracket_right_line) = await cmm.v2routines.probe_machine_pos()

  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_MACHINE_POS)
  features.setFeature("L_bracket_top_face", L_bracket_top_face)
  features.setFeature("L_bracket_back_line", L_bracket_back_line)
  features.setFeature("L_bracket_right_line", L_bracket_right_line)
  state.saveStage(Stages.PROBE_MACHINE_POS)

  csy = v2calculations.calc_part_csy(APPROX_CSY_FRONT_RIGHT_SLOT, L_bracket_top_face, L_bracket_back_line, L_bracket_right_line)

  await cmm.routines.set_part_csy(csy)
  await cmm.v2routines.go_to_clearance_y()


async def v2_calib_load_part_csy(self):
  state = CalibState.getInstance()

  features = state.getStage(Stages.PROBE_MACHINE_POS)
  L_bracket_top_face = features.L_bracket_top_face
  L_bracket_back_line = features.L_bracket_back_line
  L_bracket_right_line = features.L_bracket_right_line

  csy = calc_part_csy(APPROX_CSY_FRONT_RIGHT_SLOT, L_bracket_top_face, L_bracket_back_line, L_bracket_right_line)
  await cmm.routines.set_part_csy(csy)

def _save_zero_spindle_pos(zero_spindle_pos):
  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_SPINDLE_POS)
  features.setFeature("zero_spindle_pos", zero_spindle_pos)
  state.saveStage(Stages.PROBE_SPINDLE_POS)

#TODO check the radius of best-fit sphere here
async def v2_calib_probe_spindle_pos_v2_10(self, x, z):
  cmm = Cmm.getInstance()

  zero_spindle_pos = await cmm.v2routines.probe_spindle_pos(V2_10, x, z)
  _save_zero_spindle_pos(zero_spindle_pos)
  await cmm.v2routines.go_to_clearance_y()

#TODO check the radius of best-fit sphere here
async def v2_calib_probe_spindle_pos_v2_50(self, x, z):
  cmm = Cmm.getInstance()

  zero_spindle_pos = await cmm.v2routines.probe_spindle_pos(V2_50, x, z)
  _save_zero_spindle_pos(zero_spindle_pos)
  await cmm.v2routines.go_to_clearance_y()

async def v2_calib_verify_spindle_pos_v2_10(self):
  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = features.zero_spindle_pos

  (radius, center) = zero_spindle_pos.sphere()
  dia = 2*radius

  expected_dia = SPINDLE_BALL_DIA_10 + PROBE_DIA
  if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
    raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia))  

  logger.info("Spindle ball diameter: %s, expected: %s, diff: %s, allowed_error <= %s", dia, expected_dia, abs(dia - expected_dia), BEST_FIT_SPHERE_ERROR)
  logger.info("Spindle ball position: %s", center)

async def v2_calib_verify_spindle_pos_v2_50(self, x, z):
  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = features.zero_spindle_pos

  (radius, center) = zero_spindle_pos.sphere()
  dia = 2*radius

  expected_dia = SPINDLE_BALL_DIA_50 + PROBE_DIA
  if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
    raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia))  

  logger.info("Spindle ball diameter: %s, expected: %s, diff: %s, allowed_error <= %s", dia, expected_dia, abs(dia - expected_dia), BEST_FIT_SPHERE_ERROR)
  logger.info("Spindle ball position: %s", center)

async def v2_calib_probe_fixture_ball_pos(self, y):
  cmm = Cmm.getInstance()
  
  fixture_ball_pos = await cmm.v2routines.probe_fixture_ball_pos(APPROX_FIXTURE_BALL_HOME,y)

  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  features.setFeature("fixture_ball_pos", fixture_ball_pos)
  state.saveStage(Stages.PROBE_FIXTURE_BALL_POS)

async def v2_calib_verify_fixture_ball_pos(self):
  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)

  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  fixture_ball_pos = features.fixture_ball_pos;
  
  (radius, center) = fixture_ball_pos.sphere()

  expected_dia = FIXTURE_BALL_DIA + PROBE_DIA
  dia = 2*radius
  if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
    raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia,))

  logger.info("Fixture ball diameter: %s, expected: %s, diff: %s, allowed error <= %s", dia, expected_dia, abs(dia - expected_dia), BEST_FIT_SPHERE_ERROR)
  logger.info("Fixture ball center: %s", center)

async def v2_calib_probe_x_home(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)
  logger.debug('spindle_pos points %s, sphere %s', spindle_pos.points(), spindle_pos.sphere())

  features = state.getStage(Stages.HOMING_X)
  id = features.getNextID()
  features.setFeature(id, spindle_pos)
  state.saveStage(Stages.HOMING_X)

async def v2_calib_probe_y_home(self, y):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos_features = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  fixture_ball_pos = fixture_ball_pos_features.fixture_ball_pos;
  logger.debug('fixture_ball_pos points %s, sphere %s', fixture_ball_pos.points(), fixture_ball_pos.sphere())

  y_pos = await cmm.v2routines.probe_fixture_ball_pos(fixture_ball_pos.sphere()[1], y)

  features = state.getStage(Stages.HOMING_Y)
  id = features.getNextID()
  features.setFeature(id, y_pos)
  state.saveStage(Stages.HOMING_Y)

async def v2_calib_probe_z_home(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)
  logger.debug('spindle_pos points %s, sphere %s', spindle_pos.points(), spindle_pos.sphere())

  features = state.getStage(Stages.HOMING_Z)
  id = features.getNextID()
  features.setFeature(id, spindle_pos)
  state.saveStage(Stages.HOMING_Z)

async def v2_calib_probe_x(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)

  features = state.getStage(Stages.CHARACTERIZE_X)
  id = features.getNextID()
  features.setFeature(id, spindle_pos)
  state.saveStage(Stages.CHARACTERIZE_X)

async def v2_calib_probe_y(self, y_nominal):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_features = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  fixture_ball_pos = fixture_ball_features.fixture_ball_pos;
  logger.debug(fixture_ball_pos)
  logger.debug(fixture_ball_pos.sphere())

  y_pos = await cmm.v2routines.probe_spindle_tip(fixture_ball_pos.sphere()[1], fixture_ball_pos.sphere()[0]*2, x, z)

  features = state.getStage(Stages.CHARACTERIZE_Y)
  id = features.getNextID()
  features.setFeature(id, y_pos)
  state.saveStage(Stages.CHARACTERIZE_Y)

async def v2_calib_probe_z(self, x_nominal, z_nominal):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  logger.debug(zero_spindle_pos)
  logger.debug(zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)

  features = state.getStage(Stages.CHARACTERIZE_Z)
  id = features.getNextID()
  features.setFeature(id, spindle_pos)
  state.saveStage(Stages.CHARACTERIZE_Z)

async def v2_calib_probe_top_plane(self, y):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  logger.debug(zero_spindle_pos)
  logger.debug(zero_spindle_pos.sphere())

  top_plane = await cmm.v2routines.probe_top_plane(y)

  features = state.getStage(Stages.PROBE_TOP_PLANE)
  id = features.getNextID()
  features.setFeature(id, top_plane)
  state.saveStage(Stages.PROBE_TOP_PLANE)

LINEAR_HOMING_REPEATABILITY = 0.001 * 25.4 # 0.001 inches, 0.0254 mm

def v2_calib_verify_x_home(self):
  state = CalibState.getInstance()
  features = state.getStage(Stages.HOMING_X)

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  spindle_sphere_radius = zero_spindle_pos.sphere()[0]

  expected_dia = 2*spindle_sphere_radius
  for f in features.values():
    (rad, pos) = f.sphere()
    dia = rad*2
    if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
      raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia,))  

  feature_centers = v2calculations.calc_sphere_centers(features)
  repeatability = v2calculations.calc_max_dist_between_points(feature_centers)
  logger.info('X Homing Repeatability: %s, expected <= %s', repeatability, LINEAR_HOMING_REPEATABILITY)

  if repeatability > LINEAR_HOMING_REPEATABILITY:
    raise CalibException("X Homing repeatability failure, expected <= %s, got %s" % (LINEAR_HOMING_REPEATABILITY, repeatability))

def v2_calib_verify_z_home(self):
  state = CalibState.getInstance()
  features = state.getStage(Stages.HOMING_Z)

  state = CalibState.getInstance()
  spindle_features = state.getStage(Stages.PROBE_SPINDLE_POS)
  zero_spindle_pos = spindle_features.zero_spindle_pos;
  spindle_sphere_radius = zero_spindle_pos.sphere()[0]

  expected_dia = 2*spindle_sphere_radius
  for f in features.values():
    (rad, pos) = f.sphere()
    dia = rad*2
    if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
      raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia,))  

  feature_centers = v2calculations.calc_sphere_centers(features)
  repeatability = v2calculations.calc_max_dist_between_points(feature_centers)
  logger.info('Z Homing Repeatability: %s, expected <= %s', repeatability, LINEAR_HOMING_REPEATABILITY)

  if repeatability > LINEAR_HOMING_REPEATABILITY:
    raise CalibException("Z Homing repeatability failure, expected <= %s, got %s" % (LINEAR_HOMING_REPEATABILITY, repeatability))

def v2_calib_probe_fixture_ball(self):
  cmm = Cmm.getInstance()
  
  state = CalibState.getInstance()
  features = state.getStage(Stages.PROBE_FIXTURE_BALL)

  fixture_ball = cmm.v2routines.probe_fixture_ball_pos(APPROX_FIXTURE_BALL_HOME, 0)
  features.setFeature("fixture_ball", fixture_ball)
  state.saveStage(Stages.PROBE_FIXTURE_BALL)

def v2_calib_verify_y_home(self):
  state = CalibState.getInstance()
  features = state.getStage(Stages.HOMING_Y)

  expected_dia = FIXTURE_BALL_DIA + PROBE_DIA
  for f in features.values():
    (rad, pos) = f.sphere()
    dia = rad*2
    if abs(dia - expected_dia) > BEST_FIT_SPHERE_ERROR:
      raise CalibException("Deviation in best-fit sphere diameter. Expected %s found %s" % (expected_dia, dia,))  

  feature_centers = v2calculations.calc_sphere_centers(features)
  repeatability = v2calculations.calc_max_dist_between_points(feature_centers)
  logger.info('Y Homing Repeatability: %s, expected <= %s', repeatability, LINEAR_HOMING_REPEATABILITY)

  if repeatability > LINEAR_HOMING_REPEATABILITY:
    raise CalibException("Y Homing repeatability failure, expected <= %s, got %s" % (LINEAR_HOMING_REPEATABILITY, repeatability))

#def v2_calib_setup_cnc_csy(self):
##  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CNC_CSY)
#  pass
#

#def v2_calib_probe_spindle_at_tool_probe(self):
##  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_AT_TOOL_PROBE)
#  pass
#
#def v2_calib_probe_fixture_plane_a90(self, y_nominal):
##  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_PLANE_A90, y_nominal)
#  pass
#
#def v2_calib_tool_probe_offset(self):
##  calib.CalibManager.getInstance().run_step(calib.Steps.TOOL_PROBE_OFFSET)
#  pass
#

#def experiment_with_cmm_movement(self):
##  calib.CalibManager.getInstance().run_step(calib.Steps.EXPERIMENT_WITH_CMM_MOVEMENT)
#  pass
#
#def v2_calib_probe_home_offset_y(self, y, a, b):
##  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_Y, y, a, b)
#  pass
#
#def v2_calib_probe_home_offset_x(self, y, a, b):
##  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_X, y, a, b)
#  pass
#

#
#def v2_calib_find_pos_fixture_rel_y_perp(self, y, a, b):
#  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_Y_PERP, y, a, b)
#
#def v2_calib_find_pos_fixture_rel_x_perp(self, y, a, b):
#  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_X_PERP, y, a, b)
#
#def v2_calib_find_pos_a(self, y_nominal, a_nominal):
#  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_A, y_nominal, a_nominal)
#
#def v2_calib_find_pos_b(self, y_nominal, b_nominal):
#  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_B, y_nominal, b_nominal)
#
#def v2_calib_probe_a(self, y_nominal, a_nominal):
#  feat_name = "probe_a_%+.6f" % a_nominal
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
#
#def v2_calib_verify_probe_a(self, y_nominal, a_nominal):
#  feat_name = "verify_a_%+.6f" % a_nominal
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
#
#def v2_calib_probe_a_home(self, y_nominal, a_nominal):
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A_HOME, y_nominal, a_nominal)
#
#def v2_calib_verify_a_home(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOME)
#
#def v2_calib_verify_a_homing(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOMING)
#
#def v2_calib_probe_b(self, y_nominal, b_nominal):
#  feat_name = "probe_b_%+.6f" % b_nominal
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
#
#def v2_calib_probe_b_home(self, y_nominal, b_nominal):
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B_HOME, y_nominal, b_nominal)
#
#def v2_calib_verify_b_home(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOME)
#
#def v2_calib_verify_b_homing(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOMING)
#
#def v2_calib_verify_probe_b(self, y_nominal, b_nominal):
#  feat_name = "verify_b_%+.6f" % b_nominal
#  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
#
#def v2_calib_write_results(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_RESULTS)
#
#def v2_calib_calc_calib(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_CALIB)
#
#def v2_calib_calc_home_offsets(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_HOME_OFFSETS)
#
#def v2_calib_write_calib(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_CALIB)
#
#def v2_calib_setup_verify(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_VERIFY)
#
#def v2_calib_calc_verify(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_VERIFY)
#
#def v2_calib_write_verify(self):
#  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_VERIFY)
#
#def v2_calib_save(self):
#  cm = calib.CalibManager.getInstance()
#  cm.save_features()
#
#def v2_calib_load(self):
#  cm = calib.CalibManager.getInstance()
#  cm.load_features()
#
#def v2_calib_save_stage_probe_machine_pos(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_MACHINE_POS)
#
#def v2_calib_save_stage_probe_spindle_pos(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
#
#def v2_calib_save_stage_characterize_x(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_X)
#
#def v2_calib_save_stage_characterize_y(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Y)
#
#def v2_calib_save_stage_characterize_z(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Z)
#
#def v2_calib_save_stage_characterize_a(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_A)
#
#def v2_calib_save_stage_characterize_b(self):
#  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_B)
#
#def v2_calib_load_stage_probe_machine_pos(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_MACHINE_POS)
#
#def v2_calib_load_stage_probe_spindle_pos(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
#
#def v2_calib_load_stage_probe_fixture_ball_pos(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_FIXTURE_BALL_POS)
#
#def v2_calib_load_stage_probe_top_plane(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_TOP_PLANE)
#
#def v2_calib_load_stage_homing_x(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_X)
#
#def v2_calib_load_stage_homing_y(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Y)
#
#def v2_calib_load_stage_homing_z(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Z)
#
#def v2_calib_load_stage_homing_a(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_A)
#
#def v2_calib_load_stage_homing_b(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_B)
#
#def v2_calib_load_stage_characterize_x(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_X)
#
#def v2_calib_load_stage_characterize_y(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Y)
#
#def v2_calib_load_stage_characterize_z(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Z)
#
#def v2_calib_load_stage_characterize_a(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_A)
#
#def v2_calib_load_stage_characterize_b(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_B)
#
#def v2_calib_load_stage_tool_probe_offset(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.TOOL_PROBE_OFFSET)
#
#def v2_calib_load_stage_verify_a(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_A)
#
#def v2_calib_load_stage_verify_b(self):
#  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_B)
#
#def v2_calib_zmq_report(self):
#  calib.CalibManager.getInstance().zmq_report()
#
#def reload_calib(self):
#  cmm_disconnect(self)
#  calib.reload()
#  importlib.reload(ipp)
#  importlib.reload(ipp_tests)
#  importlib.reload(calib)
#
#def v2_calib_complete_stage(self, stage):
#  calib.CalibManager.getInstance().complete_stage(calib.Stages(int(stage)))
