import asyncio
import calib
import logging
import ipp_tests
import ipp

logger = logging.getLogger(__name__)

def v2_calib_connect(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CONNECT_TO_CMM)
  except Exception as e:
    logger.debug(e, exc_info=True)
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
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_setup_part_csy(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_PART_CSY)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_spindle_pos(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_POS, x_nominal, z_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_spindle_at_tool_probe(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_AT_TOOL_PROBE)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_fixture_ball_pos(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_BALL_POS, y_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_fixture_plane_a90(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_PLANE_A90, y_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_tool_probe_offset(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.TOOL_PROBE_OFFSET)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_setup_cnc_csy(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CNC_CSY)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_top_plane(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_TOP_PLANE, y_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def experiment_with_cmm_movement(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.EXPERIMENT_WITH_CMM_MOVEMENT)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_home_offset_y(self, y, a, b):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_Y, y, a, b)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_home_offset_x(self, y, a, b):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_X, y, a, b)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_x(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X, x_nominal, z_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_x_home(self, x_nominal, z_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X_HOME, x_nominal, z_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_x_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_X_HOME)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_y(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y, y_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_y_home(self, y_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y_HOME, y_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_y_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_Y_HOME)
  except Exception as e:
    logger.debug(e, exc_info=True)
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
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_find_pos_fixture_rel_y_perp(self, y, a, b):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_Y_PERP, y, a, b)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_find_pos_fixture_rel_x_perp(self, y, a, b):
  try:
    logger.debug('v2_calib_find_pos_fixture_rel_x_perp 1')
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_X_PERP, y, a, b)
  except Exception as e:
    logger.error("find_pos_fixture_rel_y_perp exception: %s" % str(ex), exc_info=True)
    return str(e)

def v2_calib_find_pos_a(self, y_nominal, a_nominal):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_A, y_nominal, a_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_find_pos_b(self, y_nominal, b_nominal):
  try:
    return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_B, y_nominal, b_nominal)
    logger.debug('probe_b return is %s' % r)
    return r
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_a(self, y_nominal, a_nominal):
  try:
    feat_name = "probe_a_%+.6f" % a_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_probe_a(self, y_nominal, a_nominal):
  try:
    feat_name = "verify_a_%+.6f" % a_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_a_home(self, y_nominal, a_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A_HOME, y_nominal, a_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_a_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOME)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_a_homing(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOMING)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_b(self, y_nominal, b_nominal):
  try:
    feat_name = "probe_b_%+.6f" % b_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_probe_b_home(self, y_nominal, b_nominal):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B_HOME, y_nominal, b_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_b_home(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOME)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_b_homing(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOMING)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_verify_probe_b(self, y_nominal, b_nominal):
  try:
    feat_name = "verify_b_%+.6f" % b_nominal
    calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_write_results(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_RESULTS)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_calc_calib(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CALC_CALIB)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_calc_home_offsets(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CALC_HOME_OFFSETS)
  except Exception as e:
    logger.debug(e, exc_info=True)
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
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_calc_verify(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.CALC_VERIFY)
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def v2_calib_write_verify(self):
  try:
    calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_VERIFY)
  except Exception as e:
    return str(e)

def v2_calib_save(self):
  try:
    logger.debug('v2_calib_save')
    cm = calib.CalibManager.getInstance()
    cm.save_features()
  except Exception as e:
    return str(e)

def v2_calib_load(self):
  try:
    logger.debug('v2_calib_load')
    cm = calib.CalibManager.getInstance()
    cm.load_features()
  except Exception as e:
    return str(e)

def v2_calib_save_stage_probe_machine_pos(self):
  try:
    logger.debug('v2_calib_save_stage_probe_machine_pos')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_MACHINE_POS)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_probe_spindle_pos(self):
  try:
    logger.debug('v2_calib_save_stage_probe_spindle_pos')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_x(self):
  try:
    logger.debug('v2_calib_save_stage_characterize_x')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_X)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_y(self):
  try:
    logger.debug('v2_calib_save_stage_characterize_y')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Y)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_z(self):
  try:
    logger.debug('v2_calib_save_stage_characterize_z')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Z)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_a(self):
  try:
    logger.debug('v2_calib_save_stage_characterize_a')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_A)
  except Exception as e:
    return str(e)

def v2_calib_save_stage_characterize_b(self):
  try:
    logger.debug('v2_calib_save_stage_characterize_b')
    calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_machine_pos(self):
  try:
    logger.debug('v2_calib_load_stage_probe_machine_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_MACHINE_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_spindle_pos(self):
  try:
    logger.debug('v2_calib_load_stage_probe_spindle_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_SPINDLE_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_fixture_ball_pos(self):
  try:
    logger.debug('v2_calib_load_stage_probe_fixture_ball_pos')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_FIXTURE_BALL_POS)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_probe_top_plane(self):
  try:
    logger.debug('v2_calib_load_stage_probe_top_plane')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_TOP_PLANE)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_x(self):
  try:
    logger.debug('v2_calib_load_stage_homing_x')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_X)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_y(self):
  try:
    logger.debug('v2_calib_load_stage_homing_y')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Y)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_z(self):
  try:
    logger.debug('v2_calib_load_stage_homing_z')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Z)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_a(self):
  try:
    logger.debug('v2_calib_load_stage_homing_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_homing_b(self):
  try:
    logger.debug('v2_calib_load_stage_homing_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_x(self):
  try:
    logger.debug('v2_calib_load_stage_characterize_x')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_X)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_y(self):
  try:
    logger.debug('v2_calib_load_stage_characterize_y')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Y)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_z(self):
  try:
    logger.debug('v2_calib_load_stage_characterize_z')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Z)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_a(self):
  try:
    logger.debug('v2_calib_load_stage_characterize_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_characterize_b(self):
  try:
    logger.debug('v2_calib_load_stage_characterize_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_B)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_tool_probe_offset(self):
  try:
    logger.debug('v2_calib_load_stage_tool_probe_offset')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.TOOL_PROBE_OFFSET)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_verify_a(self):
  try:
    logger.debug('v2_calib_load_stage_verify_a')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_A)
  except Exception as e:
    return str(e)

def v2_calib_load_stage_verify_b(self):
  try:
    logger.debug('v2_calib_load_stage_verify_b')
    calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_B)
  except Exception as e:
    return str(e)

def v2_calib_zmq_report(self):
  try:
    calib.CalibManager.getInstance().zmq_report()
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)

def reload_calib(self):
  cmm_disconnect(self)
  calib.reload()
  importlib.reload(ipp)
  importlib.reload(ipp_tests)
  importlib.reload(calib)

def v2_calib_complete_stage(self, stage):
  try:
    calib.CalibManager.getInstance().complete_stage(calib.Stages(int(stage)))
  except Exception as e:
    logger.debug(e, exc_info=True)
    return str(e)
