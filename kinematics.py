import math

def xyzbc_direction_local_to_global(position,dirx,diry,dirz):
  b = math.radians(position[4])
  c = math.radians(position[5])

  CB = math.cos(b)
  SB = math.sin(b)
  CC = math.cos(c)
  SC = math.sin(c)

  return ( CB*(CC*dirx-SC*diry)+SB*dirz,
           SC*dirx+CC*diry,
           -SB*(CC*dirx-SC*diry)+CB*dirz)

def xyzbc_direction_global_to_local(position,dirx,diry,dirz):
  b = -math.radians(position[4])
  c = -math.radians(position[5])

  CB = math.cos(b)
  SB = math.sin(b)
  CC = math.cos(c)
  SC = math.sin(c)

  return ( CC*(CB*dirx+SB*dirz)-SC*diry,
           SC*(CB*dirx+SB*dirz)+CC*diry,
           -SB*dirx+CB*dirz)

DIRECTION_LOCAL_TO_GLOBAL_TRANSFORM= {
  "xyzbc-trt-kins": xyzbc_direction_local_to_global
}

DIRECTION_GLOBAL_TO_LOCAL_TRANSFORM= {
  "xyzbc-trt-kins": xyzbc_direction_global_to_local
}

def transform_direction_local_to_global(kinematicsStr,position,dirx,diry,dirz):
  kinematicsArgs = kinematicsStr.split()
  kinModule = kinematicsArgs[0]

  transformFunc = DIRECTION_LOCAL_TO_GLOBAL_TRANSFORM.get(kinModule, None)

  if transformFunc:
    return transformFunc(position, dirx,diry,dirz)

  return (dirx,diry,dirz)

def transform_direction_global_to_local(kinematicsStr,position,dirx,diry,dirz):
  kinematicsArgs = kinematicsStr.split()
  kinModule = kinematicsArgs[0]

  transformFunc = DIRECTION_GLOBAL_TO_LOCAL_TRANSFORM.get(kinModule, None)

  if transformFunc:
    return transformFunc(position, dirx,diry,dirz)

  return (dirx,diry,dirz)
