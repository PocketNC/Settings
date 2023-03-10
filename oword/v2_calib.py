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
import compensation
import ini
import json
import zmq
from metrology import linePerpendicularity, angle_between, Feature, straightness

logger = logging.getLogger(__name__)

def v2_calib_verify_axes(self):
  state = CalibState.getInstance()

  xStage = state.getStage(Stages.CHARACTERIZE_X)
  yStage = state.getStage(Stages.CHARACTERIZE_Y)
  zStage = state.getStage(Stages.CHARACTERIZE_Z)

  v2verifications.verify_axes(xStage["features"], yStage["features"], zStage["features"])

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
  logger.debug("new csy %s %s %s %s %s %s", csy.x, csy.y, csy.z, csy.theta, csy.phi, csy.psi)

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

async def v2_calib_verify_spindle_pos_v2_50(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  v2verifications.verify_sphere_diameters_within_tolerance([ zero_spindle_pos ], SPINDLE_BALL_DIA_50 + PROBE_DIA)

  logger.info("Spindle ball diameter: %s", zero_spindle_pos.sphere()[0]*2)
  logger.info("Spindle ball position: %s", zero_spindle_pos.sphere()[1])

async def v2_calib_probe_fixture_ball_pos(self, y):
  """
  Probes the fixture ball using a hardcoded nominal position. The best fit position of the ball is then used
  in future stages to more accurately locate the fixture ball.
  """
  cmm = Cmm.getInstance()
  
  fixture_ball_pos = await cmm.v2routines.probe_fixture_ball_top(APPROX_FIXTURE_BALL_HOME,y,0)

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


async def v2_calib_init_probe_features_stage(self, stageFloat):
  """
  oword for initializing repetitive probing routines at certain machine positions.
  Saves a stage with a `features` key, which is a list that will be populated with Feature objects representing information about the corresponding
  position of the machine stored in the `positions` key.
  """
  logger.debug('v2_calib_init_probe_features_stage')
  state = CalibState.getInstance()
  stage = {
    "features": [],
    "positions": []
  }
  state.saveStage(int(stageFloat), stage)

async def v2_calib_save_ref(self, refValue, stageFloat):
  state = CalibState.getInstance()

  stage = state.getStage(int(stageFloat))
  stage["ref"] = refValue
  state.saveStage(int(stageFloat), stage)

  
async def v2_calib_probe_spindle(self, x, z, stageFloat):

  logger.debug("Probing spindle for stage %s", stageFloat)
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  dx = v2state.getHomeOffsetDx(state, self)
  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x+dx, z)

  stage = state.getStage(int(stageFloat))
  stage["features"].append(spindle_pos)
  stage["positions"].append({ "x": x, "z": z })
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_spindle_zero(self, x, z, stageFloat):

  logger.debug("Probing spindle zero pos for stage %s", stageFloat)
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug('zero_spindle_pos points %s, sphere %s', zero_spindle_pos.points(), zero_spindle_pos.sphere())

  dx = v2state.getHomeOffsetDx(state, self)
  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x+dx, z)

  stage = state.getStage(int(stageFloat))
  stage["zero"] = spindle_pos
  stage["zero_pos"] = { "x": x, "z": z }
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_y0(self, y, b, stageFloat):
  logger.debug("Probing fixture ball from top for y0 pos %s", stageFloat)
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  dy = v2state.getHomeOffsetDy(state, self)
  pos = await cmm.v2routines.probe_fixture_ball_top(fixture_ball_pos.sphere()[1], y+dy, b)
  
  stage = state.getStage(int(stageFloat))
  stage["zero"] = pos
  stage["zero_pos"] = { "y": y, "b": b }
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_top_plane(self, y):
  cmm = Cmm.getInstance()

  top_plane = await cmm.v2routines.probe_top_plane(y)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_OFFSETS)
  stage["top_plane"] = top_plane
  stage["y"] = y
  state.updateStage(Stages.PROBE_OFFSETS, stage)

async def v2_calib_probe_top_plane_180(self, y):
  cmm = Cmm.getInstance()

  top_plane = await cmm.v2routines.probe_top_plane(y,is_180=True)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_OFFSETS)
  stage["top_plane_180"] = top_plane
  stage["y_180"] = y
  state.updateStage(Stages.PROBE_OFFSETS, stage)

def v2_calib_verify_x_home(self):
  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)

  stage = state.getStage(Stages.HOMING_X)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], zero_spindle_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "X")
  logger.info('X Homing Repeatability: %s, expected <= %s', repeatability, expected)

def v2_calib_verify_x0_final(self):
  state = CalibState.getInstance()
  stage = state.getStage(Stages.VERIFY_OFFSETS)
  zero_spindle_pos = stage['zero']

  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  (error, max_error) = v2verifications.verify_x_homing_accuracy([zero_spindle_pos], stage["x_features"], x_dir, y_dir)
  logger.info('Final X Homing Error: %s, expected <= %s', error, max_error)

def v2_calib_verify_y0_final(self):
  state = CalibState.getInstance()
  stage = state.getStage(Stages.VERIFY_OFFSETS)
  zero_spindle_pos = stage['zero']

  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  (error, max_error) = v2verifications.verify_y_homing_accuracy([zero_spindle_pos], stage["y_features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('Final Y Homing Error: %s, expected <= %s', error, max_error)

def v2_calib_verify_y_home_final(self):
  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  stage = state.getStage(Stages.VERIFY_HOMING_Y)
  x_verify_stage = state.getStage(Stages.VERIFY_HOMING_X)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], fixture_ball_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "Y")
  logger.info('Y Homing Repeatability: %s, expected <= %s', repeatability, expected)

  probe_offsets_stage = state.getStage(Stages.PROBE_OFFSETS)
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  (error, max_error) = v2verifications.verify_y_homing_accuracy(x_verify_stage["features"], probe_offsets_stage["y_features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('Y Homing Error: %s, expected <= %s', error, max_error)

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

def v2_calib_verify_y_home(self):
  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  stage = state.getStage(Stages.HOMING_Y)
  v2verifications.verify_sphere_diameters_within_tolerance(stage["features"], fixture_ball_pos.sphere()[0]*2)

  (repeatability, expected) = v2verifications.verify_linear_homing_repeatability(stage["features"], "Y")
  logger.info('Y Homing Repeatability: %s, expected <= %s', repeatability, expected)

async def v2_calib_probe_spindle_at_tool_probe(self, x, y, z):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  zero_spindle_pos = v2state.getZeroSpindlePos(state)
  logger.debug(zero_spindle_pos)
  logger.debug(zero_spindle_pos.sphere())

  dx = v2state.getHomeOffsetDx(state, self)
  spindle_pos = await cmm.v2routines.probe_spindle_tip(zero_spindle_pos.sphere()[1], zero_spindle_pos.sphere()[0]*2, x+dx, z)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_OFFSETS)
  stage["tool_probe_pos"] = spindle_pos
  state.updateStage(Stages.PROBE_OFFSETS, stage)

async def v2_calib_probe_fixture_plane_a90(self, y, a):
  cmm = Cmm.getInstance()

  plane = await cmm.v2routines.probe_fixture_plane_a90(y)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.PROBE_OFFSETS)
  stage["plane_a90"] = plane
  stage["plane_a90_pos"] = {"y": y, "a": a}
  state.updateStage(Stages.PROBE_OFFSETS, stage)

def v2_calib_calc_tool_probe_offset(self):
  state = CalibState.getInstance()
  tool_probe_pos = v2state.getToolProbePos(state)
  plane_a90 = v2state.getPlaneA90(state)
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  tool_probe_offset = v2calculations.calc_tool_probe_offset(tool_probe_pos, plane_a90, x_dir, y_dir, z_dir, APPROX_COR)
  
  stage = state.getStage(Stages.TOOL_PROBE_OFFSET)

async def v2_calib_probe_fixture_ball_side(self, y, a, stageFloat):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  dy = v2state.getHomeOffsetDy(state,self)
  a_pos = await cmm.v2routines.probe_fixture_ball_side(fixture_ball_pos.sphere()[1], y+dy, a)

  stage = state.getStage(int(stageFloat))
  stage["features"].append(a_pos)
  stage["positions"].append({ "y": y, "a": a })
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_fixture_fin(self, y, a, stageFloat):
  cmm = Cmm.getInstance()

  line = await cmm.v2routines.probe_fixture_fin(y, a)
  logger.debug('fixture fin line points %s %s %s', line.points(), stageFloat, int(stageFloat))

  state = CalibState.getInstance()
  stage = state.getStage(int(stageFloat))
  logger.debug("stage %s", stage)
  stage["features"].append(line)
  stage["positions"].append({ "y": y, "a": a })
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_fixture_ball_top(self, y, b, stageFloat):
  """
  Probes the fixture ball with A at 0, and the provided y and b locations. Appends the data collected
  to the provided stage, which is passed in as a float (because it's passed in from G code), but is an integer
  that represents the stage to save it to. The stage is assumed to have been initialized with `v2_calib_init_probe_features_stage`.
  """
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  dy = v2state.getHomeOffsetDy(state,self)
  b_pos = await cmm.v2routines.probe_fixture_ball_top(fixture_ball_pos.sphere()[1], y+dy, b)
  
  stage = state.getStage(int(stageFloat))
  stage["features"].append(b_pos)
  stage["positions"].append({ "y": y, "b": b })
  state.updateStage(int(stageFloat), stage)


async def v2_calib_probe_a0_line(self, y, a, v2_a):
  cmm = Cmm.getInstance()
  a_line = await cmm.v2routines.probe_fixture_fin(y, a)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.CHARACTERIZE_A_LINE)
  stage["zero"] = a_line
  stage["zero_a_pos"] = v2_a
  state.updateStage(Stages.CHARACTERIZE_A_LINE, stage)
  logger.debug("SHOULD HAVER zero and zero_a_pos %s" % (stage,))

  stage = state.getStage(Stages.CHARACTERIZE_A_LINE)
  logger.debug("updated Stage %s" % (stage,))

async def v2_calib_probe_a0_sphere(self, y, a, v2_a):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  dy = v2state.getHomeOffsetDy(state, self)
  a_pos = await cmm.v2routines.probe_fixture_ball_side(fixture_ball_pos.sphere()[1], y+dy, a)

  stage = state.getStage(Stages.CHARACTERIZE_A_SPHERE)
  stage["zero"] = a_pos
  stage["zero_a_pos"] = v2_a
  state.updateStage(Stages.CHARACTERIZE_A_SPHERE, stage)


async def v2_calib_probe_b0_line(self, y, b, v2_b):
  cmm = Cmm.getInstance()
  b_line = await cmm.v2routines.probe_fixture_line(y, b)

  state = CalibState.getInstance()
  stage = state.getStage(Stages.CHARACTERIZE_B_LINE)
  stage["zero"] = b_line
  stage["zero_b_pos"] = v2_b
  state.updateStage(Stages.CHARACTERIZE_B_LINE, stage)

async def v2_calib_probe_b0_sphere(self, y, b, v2_b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  fixture_ball_pos = v2state.getFixtureBallPos(state)

  b_pos = await cmm.v2routines.probe_b_pos(fixture_ball_pos.sphere()[1], y, b)

  stage = state.getStage(Stages.CHARACTERIZE_B_SPHERE)
  stage["zero"] = b_pos
  stage["zero_b_pos"] = v2_b
  state.updateStage(Stages.CHARACTERIZE_B_SPHERE, stage)
  

async def v2_calib_find_pos_a(self, y, a):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  logger.debug(('v2_calib_find_pos_a x_dir %s, y_dir %s, z_dir %s' % (x_dir,y_dir,z_dir)))

  a_line = await cmm.v2routines.probe_fixture_fin(y, a)
  a_pos = v2calculations.calc_pos_a(a_line, x_dir, y_dir, z_dir, APPROX_COR)
  return a_pos

async def v2_calib_find_pos_b(self, y, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  b_line = await cmm.v2routines.probe_fixture_line(y, b)
  b_pos = v2calculations.calc_pos_b(b_line, x_dir, y_dir, z_dir, APPROX_COR)
  return b_pos

async def v2_calib_find_pos_b_near_home(self, y, b):
  cmm = Cmm.getInstance()

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  b_line = await cmm.v2routines.probe_fixture_line(y, b)
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

async def v2_calib_init_probe_offsets_state(self, stageFloat):
  state = CalibState.getInstance()
  stage = {
    "x_features": [],
    "x_positions": [],
    "y_features": [],
    "y_positions": []
  }
  state.saveStage(int(stageFloat), stage)


async def v2_calib_init_home_offsets_state(self):
  state = CalibState.getInstance()
  stage = {
    "x_features": [],
    "x_positions": [],
    "y_features": [],
    "y_positions": []
  }
  state.saveStage(Stages.PROBE_OFFSETS, stage)

async def v2_calib_probe_home_offset_x(self, y, a, b, stageFloat):
  cmm = Cmm.getInstance()
  feat = await cmm.v2routines.probe_home_offset_x(y, a, b)
  state = CalibState.getInstance()
  stage = state.getStage(int(stageFloat))
  stage["x_features"].append(feat)
  stage["x_positions"].append({ "y": y, "a": a, "b": b })
  state.updateStage(int(stageFloat), stage)

async def v2_calib_probe_home_offset_y(self, y, a, b, stageFloat):
  cmm = Cmm.getInstance()
  feat = await cmm.v2routines.probe_home_offset_y(y, a, b)
  state = CalibState.getInstance()
  stage = state.getStage(int(stageFloat))
  stage["y_features"].append(feat)
  stage["y_positions"].append({ "y": y, "a": a, "b": b })
  state.updateStage(int(stageFloat), stage)

def v2_calib_calc_home_offsets(self):
  pass

async def v2_calib_prep_probe_fixture_fin(self):
  cmm = Cmm.getInstance()
  await cmm.v2routines.prep_probe_fixture_fin(0,0)

async def v2_calib_report_a_position(self, y, a):
  cmm = Cmm.getInstance()
  line = await cmm.v2routines.probe_fixture_fin(0,0)
  
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  pos = v2calculations.calc_pos_a(line, x_dir, y_dir, z_dir, APPROX_COR)
  
  context = zmq.Context()
  socket = context.socket(zmq.PUSH)
  socket.set(zmq.SNDTIMEO, 3000)
  socket.bind('ipc:///tmp/cmm')
  report_json = json.dumps({'a_pos': pos})
  socket.send_string(report_json)

async def v2_calib_report_b_position(self, y, b):
  cmm = Cmm.getInstance()
  line = await cmm.v2routines.probe_fixture_line(y, b)
  
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  pos = v2calculations.calc_pos_b(line, x_dir, y_dir, z_dir, APPROX_COR)
  
  context = zmq.Context()
  socket = context.socket(zmq.PUSH)
  socket.set(zmq.SNDTIMEO, 3000)
  socket.bind('ipc:///tmp/cmm')
  report_json = json.dumps({'b_pos': pos})
  socket.send_string(report_json)

def v2_calib_verify_a_home(self, stageFloat):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(int(stageFloat))
  (repeatability, expected) = v2verifications.verify_a_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('A Homing Repeatability: %s, expected <= %s', repeatability, expected)

def v2_calib_verify_a_home_final(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.VERIFY_HOMING_A)
  (repeatability, expected) = v2verifications.verify_a_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('A Homing Repeatability: %s, expected <= %s', repeatability, expected)
  (max_error, expected) = v2verifications.verify_a_homing_accuracy(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('A Homing Max Error: %s, expected <= %s', max_error, expected)

async def v2_calib_prep_probe_b_line(self):
  cmm = Cmm.getInstance()
  await cmm.v2routines.prep_probe_b_line(0,0)

async def v2_calib_probe_fixture_line(self, y, b, stageFloat):
  cmm = Cmm.getInstance()

  line = await cmm.v2routines.probe_fixture_line(y, b)
  logger.debug('line points %s', line.points())

  state = CalibState.getInstance()
  stage = state.getStage(int(stageFloat))
  stage["features"].append(line)
  stage["positions"].append({ "y": y, "b": b })
  state.updateStage(int(stageFloat), stage)

def v2_calib_verify_b_home(self, stageFloat):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(int(stageFloat))
  (repeatability, expected) = v2verifications.verify_b_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('B Homing Repeatability: %s, expected <= %s', repeatability, expected)

def v2_calib_verify_b_home_final(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.VERIFY_HOMING_B)
  (repeatability, expected) = v2verifications.verify_b_homing_repeatability(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('B Homing Repeatability: %s, expected <= %s', repeatability, expected)
  (max_error, expected) = v2verifications.verify_b_homing_accuracy(stage["features"], x_dir, y_dir, z_dir, APPROX_COR)
  logger.info('B Homing Max Error: %s, expected <= %s', max_error, expected)

def v2_calib_calibrate(self):
  data = {}

  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  a_positions = v2state.getAPositionsLine(state)
  a_errors = []
  for (zeroed_nom_pos, pos) in a_positions:
    a_errors.append((zeroed_nom_pos, zeroed_nom_pos-pos))
  a_comp = compensation.calculateACompensation(a_errors)
  a_home_feats = v2state.getFeaturesHomingA(state)
  a_home_offset = v2calculations.calc_home_offset_a(a_home_feats, x_dir,y_dir,z_dir, APPROX_COR, a_comp[0])
  data["a_comp"] = a_comp[0].pts
  data["a_positions"] = a_positions
  data["a_errors"] = a_errors
  data["a_home_offset"] = a_home_offset

  b_positions = v2state.getBPositionsLine(state)
  b_errors = []
  for (zeroed_nom_pos, pos) in b_positions:
    if zeroed_nom_pos < 360-.000001:
      b_errors.append((zeroed_nom_pos, zeroed_nom_pos-pos))
  logger.debug("b_errors: %s", b_errors)
  b_comp = compensation.calculateBCompensation(b_errors)
  b_home_feats = v2state.getFeaturesHomingB(state)
  b_home_offset = v2calculations.calc_home_offset_b(b_home_feats, x_dir,y_dir,z_dir, APPROX_COR, b_comp[0])
  data["b_comp"] = b_comp[0].pts
  data["b_positions"] = b_positions
  data["b_errors"] = b_errors
  data["b_home_offset"] = b_home_offset

  x_homing_stage = state.getStage(Stages.HOMING_X)
  probe_offsets_stage = state.getStage(Stages.PROBE_OFFSETS)

  x_home_offset_error = v2calculations.calc_home_offset_x_error(x_dir, y_dir, x_homing_stage["features"], probe_offsets_stage["x_features"])
  current_x_home_offset = self.params["_hal[ini.0.home_offset]"]
  new_x_home_offset = current_x_home_offset - x_home_offset_error/25.4
  data["x_home_offset"] = new_x_home_offset

  y_home_offset_error = v2calculations.calc_home_offset_y_error(x_dir, y_dir, x_homing_stage["features"], probe_offsets_stage["y_features"])
  logger.debug("y_home_offset_error %s", y_home_offset_error)
  current_y_home_offset = self.params["_hal[ini.1.home_offset]"]
  new_y_home_offset = current_y_home_offset - y_home_offset_error/25.4
  data["y_home_offset"] = new_y_home_offset

  origin_spindle_pos = v2state.getOriginSpindlePos(state)

  b_table_offset = v2calculations.calc_b_table_offset(origin_spindle_pos, probe_offsets_stage["top_plane"], probe_offsets_stage["top_plane_180"], y_dir)
  data["probe_b_table_offset"] = b_table_offset

  probe_sensor_123_offset = v2calculations.calc_probe_sensor_123_offset(probe_offsets_stage["tool_probe_pos"], probe_offsets_stage["plane_a90"], z_dir)
  data["probe_sensor_123_offset"] = probe_sensor_123_offset

  state.writeCalibration(data)
  state.saveStage(Stages.CALIBRATE, data)

async def v2_calib_init_apply_calib_stage(self):
  state = CalibState.getInstance()

def v2_calib_calc_a_comp(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  characterize_stage = state.getStage(Stages.CHARACTERIZE_A_LINE)
  
  zero_feat = characterize_stage['zero']
  zero_pos = v2calculations.calc_pos_a(zero_feat, x_dir, y_dir, z_dir, APPROX_COR)
  nom_zero_pos = characterize_stage['zero_a_pos']

  angles = []
  errors = []

  for (feat, nom_pos) in zip(characterize_stage["features"],characterize_stage["positions"]):
    zeroed_nom_pos = nom_pos - nom_zero_pos
    a_pos = v2calculations.calc_pos_a(feat, x_dir, y_dir, z_dir, APPROX_COR)
    angles.append((zeroed_nom_pos, a_pos))
    err = zeroed_nom_pos - a_pos 
    errors.append((zeroed_nom_pos, a_pos))

  a_comp = compensation.calculateACompensation(errors)

  stage = state.getStage(Stages.CALIBRATE)
  stage["a_err"] = errors
  stage["a_comp"] = a_comp
  state.updateStage(Stages.CALIBRATE, stage)


def v2_calib_calc_b_comp(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  characterize_stage = state.getStage(Stages.CHARACTERIZE_B_LINE)
  
  zero_feat = characterize_stage['zero']
  zero_pos = v2calculations.calc_pos_b(zero_feat, x_dir, y_dir, z_dir, APPROX_COR)
  nom_zero_pos = characterize_stage['zero_b_pos']

  angles = []
  errors = []

  for (feat, nom_pos) in zip(characterize_stage["features"],characterize_stage["positions"]):
    zeroed_nom_pos = nom_pos - nom_zero_pos
    b_pos = v2calculations.calc_pos_b(feat, x_dir, y_dir, z_dir, APPROX_COR)
    angles.append((zeroed_nom_pos, b_pos))
    err = zeroed_nom_pos - b_pos 
    errors.append((zeroed_nom_pos, b_pos))

  b_comp = compensation.calculateBCompensation(errors)
  
  stage = state.getStage(Stages.CALIBRATE)
  stage["b_err"] = errors
  stage["b_comp"] = b_comp
  state.updateStage(Stages.CALIBRATE, stage)

def v2_calib_verify_a(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.VERIFY_A_LINE)
  
  angles = []
  errors = []

  for (feat, nom_pos) in zip(stage["features"],stage["positions"]):
    a_pos = v2calculations.calc_pos_a(feat, x_dir, y_dir, z_dir, APPROX_COR)
    angles.append((nom_pos['a'], a_pos))
    err = nom_pos['a'] - a_pos 
    errors.append((nom_pos['a'], err))

  (max_err_pair, expected) = v2verifications.verify_rotary_accuracy(errors, 'A')
  logger.info('A max err pass: %s, expected <= %s. Max err pos %s', max_err_pair[1], expected, max_err_pair[0])

def v2_calib_verify_b(self):
  state = CalibState.getInstance()
  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)
  stage = state.getStage(Stages.VERIFY_B_LINE)
  
  angles = []
  errors = []

  for (feat, nom_pos) in zip(stage["features"],stage["positions"]):
    b_pos = v2calculations.calc_pos_b(feat, x_dir, y_dir, z_dir, APPROX_COR)

    if b_pos-nom_pos['b'] > 180:
      b_pos -= 360
    elif b_pos-nom_pos['b'] < -180:
      b_pos += 360

    angles.append((nom_pos['b'], b_pos))
    err = nom_pos['b'] - b_pos 
    errors.append((nom_pos['b'], err))

  (max_err_pair, expected) = v2verifications.verify_rotary_accuracy(errors, 'B')
  logger.info('B max err pass: %s, expected <= %s. Max err pos %s', max_err_pair[1], expected, max_err_pair[0])

