"""
`oword`s for interacting with calibration routines.
"""
import logging
from cmmmanager import Cmm
from ipp import Csy
import v2calculations
import v2state
import v2verifications
from calibstate import CalibState, Stages
from v2routines import V2_10, V2_50, PROBE_DIA, SPINDLE_BALL_DIA_10, SPINDLE_BALL_DIA_50, APPROX_FIXTURE_BALL_HOME, FIXTURE_BALL_DIA, APPROX_COR
import numpy as np

logger = logging.getLogger(__name__)

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

  stage = {}
  stage["L_bracket_top_face"] = L_bracket_top_face
  stage["L_bracket_back_line"] = L_bracket_back_line
  stage["L_bracket_right_line"] = L_bracket_right_line
  state.saveStage(Stages.PROBE_MACHINE_POS, stage)

  csy = v2calculations.calc_part_csy(APPROX_CSY_FRONT_RIGHT_SLOT, L_bracket_top_face, L_bracket_back_line, L_bracket_right_line)

  await cmm.routines.set_part_csy(csy)
  await cmm.v2routines.go_to_clearance_y()


async def v2_calib_load_part_csy(self):
  state = CalibState.getInstance()

  stage = state.getStage(Stages.PROBE_MACHINE_POS)

  L_bracket_top_face = stage["L_bracket_top_face"]
  L_bracket_back_line = stage["L_bracket_back_line"]
  L_bracket_right_line = stage["L_bracket_right_line"]

  csy = calc_part_csy(APPROX_CSY_FRONT_RIGHT_SLOT, L_bracket_top_face, L_bracket_back_line, L_bracket_right_line)
  await cmm.routines.set_part_csy(csy)

def _save_zero_spindle_pos(zero_spindle_pos):
  state = CalibState.getInstance()

  stage = {}
  stage["zero_spindle_pos"] = zero_spindle_pos

  state.saveStage(Stages.PROBE_SPINDLE_POS, stage)

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
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  v2verifications.verify_sphere_diameters_within_tolerance([ zero_spindle_pos ], SPINDLE_BALL_DIA_10 + PROBE_DIA)

  logger.info("Spindle ball diameter: %s", zero_spindle_pos.sphere()[0]*2)
  logger.info("Spindle ball position: %s", zero_spindle_pos.sphere()[1])

async def v2_calib_verify_spindle_pos_v2_50(self, x, z):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  v2verifications.verify_sphere_diameters_within_tolerance([ zero_spindle_pos ], SPINDLE_BALL_DIA_50 + PROBE_DIA)

  logger.info("Spindle ball diameter: %s", zero_spindle_pos.sphere()[0]*2)
  logger.info("Spindle ball position: %s", zero_spindle_pos.sphere()[1])

async def v2_calib_probe_fixture_ball_pos(self, y):
  cmm = Cmm.getInstance()
  
  fixture_ball_pos = await cmm.v2routines.probe_fixture_ball_top(APPROX_FIXTURE_BALL_HOME,y)

  state = CalibState.getInstance()

  stage = {}
  stage["fixture_ball_pos"] = fixture_ball_pos

  state.saveStage(Stages.PROBE_FIXTURE_BALL_POS, stage)

async def v2_calib_verify_fixture_ball_pos(self):
  state = CalibState.getInstance()

  stage = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  fixture_ball_pos = stage["fixture_ball_pos"]
  
  v2verifications.verify_sphere_diameters_within_tolerance([ fixture_ball_pos ], FIXTURE_BALL_DIA + PROBE_DIA)

  logger.info("Fixture ball diameter: %s", fixture_ball_pos.sphere()[0]*2)
  logger.info("Fixture ball center: %s", fixture_ball_pos.sphere()[1])

async def v2_calib_init_x_home_state(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.HOMING_X, stage)

async def v2_calib_init_y_home_state(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.HOMING_Y, stage)

async def v2_calib_init_z_home_state(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.HOMING_Z, stage)
  
async def v2_calib_probe_x_home(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)
  logger.debug('spindle_pos points %s, sphere %s', spindle_pos.points(), spindle_pos.sphere())

  stage = state.getStage(Stages.HOMING_X)
  stage["features"].append(spindle_pos)
  stage["positions"].append({ "x": x, "z": z })
  state.saveStage(Stages.HOMING_X, stage)

async def v2_calib_probe_y_home(self, y):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos_stage = state.getStage(Stages.PROBE_FIXTURE_BALL_POS)
  fixture_ball_pos = fixture_ball_pos_stage["fixture_ball_pos"]
  logger.debug('fixture_ball_pos points %s, sphere %s', fixture_ball_pos.points(), fixture_ball_pos.sphere())

  y_pos = await cmm.v2routines.probe_fixture_ball_top(fixture_ball_pos.sphere()[1], y)

  stage = state.getStage(Stages.HOMING_Y)
  stage["features"].append(y_pos)
  stage["positions"].append({ "y": y })
  state.saveStage(Stages.HOMING_Y, stage)

async def v2_calib_probe_z_home(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)
  logger.debug('spindle_pos points %s, sphere %s', spindle_pos.points(), spindle_pos.sphere())

  stage = state.getStage(Stages.HOMING_Z)
  stage["features"].append(spindle_pos)
  stage["positions"].append({ "x": x, "z": z })
  state.saveStage(Stages.HOMING_Z, stage)

async def v2_calib_init_characterize_x(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.CHARACTERIZE_X, stage)

async def v2_calib_init_characterize_y(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.CHARACTERIZE_Y, stage)

async def v2_calib_init_characterize_z(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.CHARACTERIZE_Z, stage)

async def v2_calib_init_characterize_a(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.CHARACTERIZE_A, stage)

async def v2_calib_init_characterize_b(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.CHARACTERIZE_B, stage)

async def v2_calib_probe_x(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)

  stage = state.getStage(Stages.CHARACTERIZE_X)
  stage["features"].append(spindle_pos)
  stage["positions"].append({ "x": x, "z": z })
  state.saveStage(Stages.CHARACTERIZE_X, stage)

async def v2_calib_probe_y(self, y):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  y_pos = await cmm.v2routines.probe_fixture_ball_top(fixture_ball_pos.sphere()[1], y)

  stage = state.getStage(Stages.CHARACTERIZE_Y)
  stage["features"].append(y_pos)
  stage["positions"].append({ "y": y })
  state.saveStage(Stages.CHARACTERIZE_Y, stage)

async def v2_calib_probe_z(self, x, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug(zero_spindle_pos)
  logger.debug(zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)

  stage = state.getStage(Stages.CHARACTERIZE_Z)
  stage["features"].append(spindle_pos)
  stage["positions"].append({ "x": x, "z": z })
  state.saveStage(Stages.CHARACTERIZE_Z, stage)

async def v2_calib_probe_top_plane(self, y):
  cmm = Cmm.getInstance()

  top_plane = await cmm.v2routines.probe_top_plane(y)

  state = CalibState.getInstance()
  stage = {}
  stage["top_plane"] = top_plane
  stage["y"] = y
  state.saveStage(Stages.PROBE_TOP_PLANE, stage)

def v2_calib_verify_x_home(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  stage = state.getStage(Stages.HOMING_X)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], zero_spindle_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "X")
  logger.info('X Homing Repeatability: %s, expected <= %s', repeatability, expected)

def v2_calib_verify_z_home(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  stage = state.getStage(Stages.HOMING_Z)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], zero_spindle_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "Z")
  logger.info('Z Homing Repeatability: %s, expected <= %s', repeatability, expected)

def v2_calib_verify_characterize_z(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  stage = state.getStage(Stages.CHARACTERIZE_Z)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], zero_spindle_pos.sphere()[0]*2)

  z_dir = v2state.getZDirection(state)
  logger.info('Z Direction: %s', z_dir)
  v2verifications.verify_linear_axis_direction(z_dir, (0,0,1))

def v2_calib_verify_characterize_x(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  stage = state.getStage(Stages.CHARACTERIZE_X)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], zero_spindle_pos.sphere()[0]*2)

  x_dir = v2state.getXDirection(state)
  logger.info('X Direction: %s', x_dir)
  v2verifications.verify_linear_axis_direction(x_dir, (1,0,0))

def v2_calib_verify_characterize_y(self):
  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  stage = state.getStage(Stages.CHARACTERIZE_Y)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], fixture_ball_pos.sphere()[0]*2)

  y_dir = v2state.getYDirection(state)
  logger.info('Y Direction: %s', y_dir)
  v2verifications.verify_linear_axis_direction(y_dir, (0,1,0))

def v2_calib_probe_fixture_ball(self):
  cmm = Cmm.getInstance()
  
  y = 0
  state = CalibState.getInstance()
  fixture_ball = cmm.v2routines.probe_fixture_ball_top(APPROX_FIXTURE_BALL_HOME, y)

  stage = {
    "fixture_ball": fixture_ball,
    "position": { "y": y }
  }

  state.saveStage(Stages.PROBE_FIXTURE_BALL, stage)

def v2_calib_verify_y_home(self):
  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  stage = state.getStage(Stages.HOMING_Y)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], fixture_ball_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "Y")
  logger.info('Y Homing Repeatability: %s, expected <= %s', repeatability, expected)


async def v2_calib_prep_probe_fixture_ball(self):
  cmm = Cmm.getInstance()
  await cmm.v2routines.prep_probe_fixture_ball(0,0)


async def v2_calib_probe_spindle_at_tool_probe(self, x, y, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug(zero_spindle_pos)
  logger.debug(zero_spindle_pos.sphere())

  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x, z)

  state = CalibState.getInstance()
  stage = {}
  stage["tool_probe_pos"] = spindle_pos
  state.saveStage(Stages.TOOL_PROBE_OFFSET, stage)

async def v2_calib_probe_fixture_plane_a90(self, y):
  cmm = Cmm.getInstance()

  plane = await cmm.v2routines.probe_fixture_plane_a90(y)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.TOOL_PROBE_OFFSET)
  stage["plane_a90"] = plane
  state.saveStage(Stages.TOOL_PROBE_OFFSET, stage)

def v2_calib_calc_tool_probe_offset(self):
  state = CalibState.getInstance()
  tool_probe_pos = v2state.getToolProbePos(state)
  plane_a90 = v2state.getPlaneA90(state)
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  tool_probe_offset = v2calculations.calc_tool_probe_offset(tool_probe_pos, plane_a90, x_dir, y_dir, z_dir, APPROX_COR)
  
  stage = state.getStage(Stages.TOOL_PROBE_OFFSET)

  

async def v2_calib_probe_a0(self, y, a, v2_a):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  a_pos = await cmm.v2routines.probe_fixture_ball_side(fixture_ball_pos.sphere()[1], y, a)

  stage = state.getStage(Stages.CHARACTERIZE_A)
  stage["zero"] = a_pos
  stage["zero_a_pos"] = v2_a
  state.saveStage(Stages.CHARACTERIZE_A, stage)

async def v2_calib_probe_a(self, y, a):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  a_pos = await cmm.v2routines.probe_fixture_ball_side(fixture_ball_pos.sphere()[1], y, a)

  stage = state.getStage(Stages.CHARACTERIZE_A)
  stage["features"].append(a_pos)
  stage["positions"].append({ "y": y, "a": a })
  state.saveStage(Stages.CHARACTERIZE_A, stage)

async def v2_calib_probe_b(self, y, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  b_pos = await cmm.v2routines.probe_b_pos(fixture_ball_pos.sphere()[1], y, b)
  
  stage = state.getStage(Stages.CHARACTERIZE_B)
  stage["features"].append(b_pos)
  stage["positions"].append({ "y": y, "b": b })
  state.saveStage(Stages.CHARACTERIZE_B, stage)

async def v2_calib_find_pos_a(self, y, a):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  a_line = await cmm.v2routines.probe_a_line(y, a)
  a_pos = v2calculations.calc_pos_a(a_line, x_dir, y_dir, z_dir, APPROX_COR)
  return a_pos

async def v2_calib_find_pos_b(self, y, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  b_line = await cmm.v2routines.probe_b_line(y, b)
  b_pos = v2calculations.calc_pos_b(b_line, x_dir, y_dir, z_dir, APPROX_COR)
  return b_pos

async def v2_calib_find_pos_b_near_home(self, y, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  b_line = await cmm.v2routines.probe_b_line(y, b)
  b_pos = v2calculations.calc_pos_b(b_line, x_dir, y_dir, z_dir, APPROX_COR)
  if b_pos > 180:
    b_pos = b_pos - 360
  return b_pos

async def v2_calib_find_pos_fixture_rel_x_perp(self, y, a, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  vert_fixture_line = await cmm.v2routines.probe_fixture_vertical(y)
  angle_rel_x = v2calculations.calc_ccw_angle_from_x(vert_fixture_line, x_dir, y_dir, z_dir, APPROX_COR)
  return angle_rel_x + 90

async def v2_calib_find_pos_fixture_rel_y_perp(self, y, a, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  horiz_fixture_line = await cmm.v2routines.probe_fixture_horizontal(y)
  angle_rel_y = v2calculations.calc_ccw_angle_from_y(horiz_fixture_line, x_dir, y_dir, z_dir, APPROX_COR)
  return angle_rel_y + 90

async def v2_calib_init_home_offsets_state(self):
  state = CalibState.getInstance()
  stage = {
    "x_features": [],
    "x_positions": [],
    "y_features": [],
    "y_positions": []
  }
  state.saveStage(Stages.PROBE_HOME_OFFSETS, stage)

async def v2_calib_probe_home_offset_x(self, y, a, b):
  cmm = Cmm.getInstance()
  feat = await cmm.v2routines.probe_home_offset_x(y, a, b)
  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_HOME_OFFSETS)
  stage["x_features"].append(feat)
  stage["x_positions"].append({ "y": y, "a": a, "b": b })
  state.saveStage(Stages.PROBE_HOME_OFFSETS, stage)

async def v2_calib_probe_home_offset_y(self, y, a, b):
  cmm = Cmm.getInstance()
  feat = await cmm.v2routines.probe_home_offset_y(y, a, b)
  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_HOME_OFFSETS)
  stage["y_features"].append(feat)
  stage["y_positions"].append({ "y": y, "a": a, "b": b })
  state.saveStage(Stages.PROBE_HOME_OFFSETS, stage)

def v2_calib_calc_home_offsets(self):
  pass

async def v2_calib_init_a_home_state(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.HOMING_A, stage)

async def v2_calib_prep_probe_fixture_fin(self):
  cmm = Cmm.getInstance()
  await cmm.v2routines.prep_probe_fixture_fin(0,0)


async def v2_calib_probe_a_home(self, y, a):
  cmm = Cmm.getInstance()

  a_line = await cmm.v2routines.probe_a_line(y, a)
  logger.debug('a_line points %s', a_line.points())

  state = CalibState.getInstance()
  stage = state.getStage(Stages.HOMING_A)
  stage["features"].append(a_line)
  stage["positions"].append({ "y": y, "a": a })
  state.saveStage(Stages.HOMING_A, stage)

def v2_calib_verify_a_home(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.HOMING_A)
  (repeatability, expected) = v2verifications.verify_a_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('A Homing Repeatability: %s, expected <= %s', repeatability, expected)

async def v2_calib_init_b_home_state(self):
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(Stages.HOMING_B, stage)

async def v2_calib_prep_probe_b_line(self):
  cmm = Cmm.getInstance()
  await cmm.v2routines.prep_probe_b_line(0,0)

async def v2_calib_probe_b_home(self, y, b):
  cmm = Cmm.getInstance()

  b_line = await cmm.v2routines.probe_b_line(y, b)
  logger.debug('b_line points %s', b_line.points())

  state = CalibState.getInstance()
  stage = state.getStage(Stages.HOMING_B)
  stage["features"].append(b_line)
  stage["positions"].append({ "y": y, "b": b })
  state.saveStage(Stages.HOMING_B, stage)

def v2_calib_verify_b_home(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.HOMING_B)
  (repeatability, expected) = v2verifications.verify_b_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('B Homing Repeatability: %s, expected <= %s', repeatability, expected)


#def v2_calib_setup_cnc_csy(self):
##  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CNC_CSY)
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
##
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
