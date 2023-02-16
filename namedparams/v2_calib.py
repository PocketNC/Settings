from calibstate import Stages, CalibState

def _v2_calib_x_offset(self):
  state = CalibState.getInstance()
  return state.getHomeOffsetDx(state,self)

def _v2_calib_y_offset(self):
  state = CalibState.getInstance()
  return state.getHomeOffsetDy(state,self)

__all__ = [ k for k in globals().keys() if k.startswith("_v2_calib") ]

for n in Stages:
  var_name = ('_CALIB_%s' % n.name).lower()
  __all__.append(var_name)
  globals()[var_name] = (lambda name: (lambda self: Stages[name].value))(n.name)
