import asyncio
import calib
import logging
import ipp_tests
import ipp

logger = logging.getLogger(__name__)

def v2_calib_connect(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.CONNECT_TO_CMM)

def v2_calib_disconnect(self):
  cm = calib.CalibManager.getInstance()
  if cm.client and cm.client.is_connected():
    cm.run_step(calib.Steps.DISCONNECT_FROM_CMM)


def v2_calib_probe_machine_pos(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_MACHINE_POS)

def v2_calib_setup_part_csy(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_PART_CSY)

def v2_calib_probe_spindle_pos(self, x_nominal, z_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_POS, x_nominal, z_nominal)

def v2_calib_probe_spindle_at_tool_probe(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_SPINDLE_AT_TOOL_PROBE)

def v2_calib_probe_fixture_ball_pos(self, y_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_BALL_POS, y_nominal)

def v2_calib_probe_fixture_plane_a90(self, y_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_FIXTURE_PLANE_A90, y_nominal)

def v2_calib_tool_probe_offset(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.TOOL_PROBE_OFFSET)

def v2_calib_setup_cnc_csy(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_CNC_CSY)

def v2_calib_probe_top_plane(self, y_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_TOP_PLANE, y_nominal)

def experiment_with_cmm_movement(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.EXPERIMENT_WITH_CMM_MOVEMENT)

def v2_calib_probe_home_offset_y(self, y, a, b):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_Y, y, a, b)

def v2_calib_probe_home_offset_x(self, y, a, b):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_HOME_OFFSET_X, y, a, b)

def v2_calib_probe_x(self, x_nominal, z_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X, x_nominal, z_nominal)

def v2_calib_probe_x_home(self, x_nominal, z_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_X_HOME, x_nominal, z_nominal)

def v2_calib_verify_x_home(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_X_HOME)

def v2_calib_probe_y(self, y_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y, y_nominal)

def v2_calib_probe_y_home(self, y_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Y_HOME, y_nominal)

def v2_calib_verify_y_home(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_Y_HOME)

def v2_calib_probe_z(self, x_nominal, z_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Z, x_nominal, z_nominal)

def v2_calib_probe_z_home(self, x_nominal, z_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_Z_HOME, x_nominal, z_nominal)

def v2_calib_verify_z_home(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_Z_HOME)

def v2_calib_find_pos_fixture_rel_y_perp(self, y, a, b):
  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_Y_PERP, y, a, b)

def v2_calib_find_pos_fixture_rel_x_perp(self, y, a, b):
  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_FIXTURE_REL_X_PERP, y, a, b)

def v2_calib_find_pos_a(self, y_nominal, a_nominal):
  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_A, y_nominal, a_nominal)

def v2_calib_find_pos_b(self, y_nominal, b_nominal):
  return calib.CalibManager.getInstance().run_step(calib.Steps.FIND_POS_B, y_nominal, b_nominal)

def v2_calib_probe_a(self, y_nominal, a_nominal):
  feat_name = "probe_a_%+.6f" % a_nominal
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)

def v2_calib_verify_probe_a(self, y_nominal, a_nominal):
  feat_name = "verify_a_%+.6f" % a_nominal
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A, feat_name, y_nominal, a_nominal)

def v2_calib_probe_a_home(self, y_nominal, a_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_A_HOME, y_nominal, a_nominal)

def v2_calib_verify_a_home(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOME)

def v2_calib_verify_a_homing(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_A_HOMING)

def v2_calib_probe_b(self, y_nominal, b_nominal):
  feat_name = "probe_b_%+.6f" % b_nominal
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)

def v2_calib_probe_b_home(self, y_nominal, b_nominal):
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B_HOME, y_nominal, b_nominal)

def v2_calib_verify_b_home(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOME)

def v2_calib_verify_b_homing(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.VERIFY_B_HOMING)

def v2_calib_verify_probe_b(self, y_nominal, b_nominal):
  feat_name = "verify_b_%+.6f" % b_nominal
  calib.CalibManager.getInstance().run_step(calib.Steps.PROBE_B, feat_name, y_nominal, b_nominal)

def v2_calib_write_results(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_RESULTS)

def v2_calib_calc_calib(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_CALIB)

def v2_calib_calc_home_offsets(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_HOME_OFFSETS)

def v2_calib_write_calib(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_CALIB)

def v2_calib_setup_verify(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.SETUP_VERIFY)

def v2_calib_calc_verify(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.CALC_VERIFY)

def v2_calib_write_verify(self):
  calib.CalibManager.getInstance().run_step(calib.Steps.WRITE_VERIFY)

def v2_calib_save(self):
  cm = calib.CalibManager.getInstance()
  cm.save_features()

def v2_calib_load(self):
  cm = calib.CalibManager.getInstance()
  cm.load_features()

def v2_calib_save_stage_probe_machine_pos(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_MACHINE_POS)

def v2_calib_save_stage_probe_spindle_pos(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.PROBE_SPINDLE_POS)

def v2_calib_save_stage_characterize_x(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_X)

def v2_calib_save_stage_characterize_y(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Y)

def v2_calib_save_stage_characterize_z(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_Z)

def v2_calib_save_stage_characterize_a(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_A)

def v2_calib_save_stage_characterize_b(self):
  calib.CalibManager.getInstance().save_stage_progress(calib.Stages.CHARACTERIZE_B)

def v2_calib_load_stage_probe_machine_pos(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_MACHINE_POS)

def v2_calib_load_stage_probe_spindle_pos(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_SPINDLE_POS)

def v2_calib_load_stage_probe_fixture_ball_pos(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_FIXTURE_BALL_POS)

def v2_calib_load_stage_probe_top_plane(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.PROBE_TOP_PLANE)

def v2_calib_load_stage_homing_x(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_X)

def v2_calib_load_stage_homing_y(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Y)

def v2_calib_load_stage_homing_z(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_Z)

def v2_calib_load_stage_homing_a(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_A)

def v2_calib_load_stage_homing_b(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.HOMING_B)

def v2_calib_load_stage_characterize_x(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_X)

def v2_calib_load_stage_characterize_y(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Y)

def v2_calib_load_stage_characterize_z(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_Z)

def v2_calib_load_stage_characterize_a(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_A)

def v2_calib_load_stage_characterize_b(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.CHARACTERIZE_B)

def v2_calib_load_stage_tool_probe_offset(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.TOOL_PROBE_OFFSET)

def v2_calib_load_stage_verify_a(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_A)

def v2_calib_load_stage_verify_b(self):
  calib.CalibManager.getInstance().load_stage_progress(calib.Stages.VERIFY_B)

def v2_calib_zmq_report(self):
  calib.CalibManager.getInstance().zmq_report()

def reload_calib(self):
  cmm_disconnect(self)
  calib.reload()
  importlib.reload(ipp)
  importlib.reload(ipp_tests)
  importlib.reload(calib)

def v2_calib_complete_stage(self, stage):
  calib.CalibManager.getInstance().complete_stage(calib.Stages(int(stage)))
