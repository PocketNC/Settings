from calibstate import Stages, CalibState
import v2state
import v2calculations

def _v2_calib_x_offset(self):
  state = CalibState.getInstance()
  x_homing_stage = state.getStage(Stages.HOMING_X)
  probe_offsets_stage = state.getStage(Stages.PROBE_OFFSETS)

  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  return v2calculations.calc_home_offset_x_error(x_dir, y_dir, z_dir, x_homing_stage["features"], probe_offsets_stage["x_features"])/25.4

def _v2_calib_y_offset(self):
  state = CalibState.getInstance()
  x_homing_stage = state.getStage(Stages.HOMING_X)
  probe_offsets_stage = state.getStage(Stages.PROBE_OFFSETS)

  (x_dir,y_dir,z_dir) = v2state.getAxisDirections(state)

  return v2calculations.calc_home_offset_y_error(x_dir, y_dir, z_dir, x_homing_stage["features"], probe_offsets_stage["y_features"])/25.4

__all__ = [ k for k in globals().keys() if k.startswith("_v2_calib") ]

for n in Stages:
  var_name = ('_CALIB_%s' % n.name).lower()
  __all__.append(var_name)
  globals()[var_name] = (lambda name: (lambda self: Stages[name].value))(n.name)
