import metrology

def add_point(self, x=0, y=0, z=0):
  manager = metrology.FeatureManager.getInstance()
  feature = manager.getActiveFeature()
  feature.addPoint(x,y,z)

def clear_points(self):
  manager = metrology.FeatureManager.getInstance()
  feature = manager.getActiveFeature()
  feature.clearPoints()

def set_active_feature(self, id):
  manager = metrology.FeatureManager.getInstance()
  manager.setActiveFeatureID(id)
