import calib

__all__ = []
for n in calib.Stages:
  var_name = '_CALIB_%s' % n.name
  __all__.append(var_name)
  globals()[var_name] = (lambda name: (lambda self: calib.Stages[name].value))(n.name)
