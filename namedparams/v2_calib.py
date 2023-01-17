from calibstate import Stages

__all__ = []
for n in Stages:
  var_name = ('_CALIB_%s' % n.name).lower()
  __all__.append(var_name)
  globals()[var_name] = (lambda name: (lambda self: Stages[name].value))(n.name)
