// Copyright 2018 PocketNC (john@pocketnc.com)
// Copyright 2016 Rudy du Preez <rudy@asmsa.co.za>
/********************************************************************
 * Description: pocketnckins.c
 * Kinematics for 5 axis mill named pocketnc.
 * Adapted from 5 axis mill named XYZAC and the basic trivkins
 * This mill has a tilting table (A axis) and horizontal rotary
 * mounted to the table (B axis). The kinematics can switch between
 * 5 axis kinematics and trivial kinematics by setting the hal pin 
 * pocketnckins.five-axis-kinematics to 1 or 0.
 *
 * Authors: Rudy du Preez <rudy@asmsa.co.za>
 *          John Allwine <john@pocketnc.com>
 * License: GPL Version 2
 *
 ********************************************************************/
//
//This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

#include "kinematics.h" /* these decls */
#include "posemath.h"
#include "hal.h"
#include "rtapi.h"
#include "rtapi_math.h"

#define VTVERSION VTKINEMATICS_VERSION1

#define JX 0
#define JY 1
#define JZ 2

#define JA 3
#define JB 4

#define NUM_JOINTS 5

struct haldata {
  hal_bit_t *five_axis_kinematics;
  hal_float_t *tool_z_offset;

  hal_bit_t *carte_space_changed;
  hal_bit_t *carte_space_change_ok;

  hal_float_t *pos_x;
  hal_float_t *pos_y;
  hal_float_t *pos_z;
} *haldata;

typedef struct {
  int five_axis_kinematics;
  float tool_z_offset;
} KinematicsState;

static KinematicsState current_state;

int kinematicsForwardFromState(const KinematicsState state, 
    const double *joints,
    EmcPose * pos,
    const KINEMATICS_FORWARD_FLAGS * fflags,
    KINEMATICS_INVERSE_FLAGS * iflags) {

  if(state.five_axis_kinematics) {
    double a_rad = joints[JA]*M_PI/180;
    double b_rad = joints[JB]*M_PI/180;

    double CA = rtapi_cos(a_rad);
    double SA = rtapi_sin(a_rad);

    double CB = rtapi_cos(b_rad);
    double SB = rtapi_sin(b_rad);

    double Lz = state.tool_z_offset;

    pos->tran.x = joints[JX]*CB + joints[JY]*SB*SA - (joints[JZ]-Lz)*SB*CA;
    pos->tran.y = joints[JY]*CA + (joints[JZ]-Lz)*SA;
    pos->tran.z = joints[JX]*SB - joints[JY]*CB*SA + (joints[JZ]-Lz)*CB*CA+Lz;

    pos->a = joints[JA];
    pos->b = joints[JB];
  } else {
    pos->tran.x = joints[0];
    pos->tran.y = joints[1];
    pos->tran.z = joints[2];
    pos->a = joints[3];
    pos->b = joints[4];
  }

  return 0;
}

static int kinematicsForward(const double *joints,
    EmcPose * pos,
    const KINEMATICS_FORWARD_FLAGS * fflags,
    KINEMATICS_INVERSE_FLAGS * iflags)
{
  if(current_state.five_axis_kinematics != *(haldata->five_axis_kinematics)
      || (current_state.tool_z_offset-*(haldata->tool_z_offset)) < -.00001
      || current_state.tool_z_offset-*(haldata->tool_z_offset) > .00001) {
    *(haldata->carte_space_changed) = 1;
    rtapi_print_msg(RTAPI_MSG_INFO, "parameters changed in pocketnckins\n");
  }

  if(*(haldata->carte_space_change_ok)) {
    rtapi_print_msg(RTAPI_MSG_INFO, "detected space change is ok, changing current_state\n");

    current_state.five_axis_kinematics = *(haldata->five_axis_kinematics);
    current_state.tool_z_offset = *(haldata->tool_z_offset);
    *(haldata->carte_space_changed) = 0;
  }

  kinematicsForwardFromState(current_state, joints, pos, fflags, iflags);

  if(*(haldata->carte_space_change_ok)) {
    *(haldata->pos_x) = pos->tran.x;
    *(haldata->pos_y) = pos->tran.y;
    *(haldata->pos_z) = pos->tran.z-current_state.tool_z_offset;
  }

  return 0;
}

int kinematicsInverseFromState(const KinematicsState state, 
    const EmcPose * pos,
    double *joints,
    const KINEMATICS_INVERSE_FLAGS * iflags,
    KINEMATICS_FORWARD_FLAGS * fflags)
{

  if(state.five_axis_kinematics) {
    double a_rad = pos->a*M_PI/180;
    double b_rad = pos->b*M_PI/180;

    double CA = rtapi_cos(a_rad);
    double SA = rtapi_sin(a_rad);

    double CB = rtapi_cos(b_rad);
    double SB = rtapi_sin(b_rad);

    double Lz = state.tool_z_offset;

    joints[JX] = pos->tran.x*CB + (pos->tran.z)*SB - Lz*SB;
    joints[JY] = pos->tran.x*SB*SA + pos->tran.y*CA - (pos->tran.z)*CB*SA + Lz*CB*SA;
    joints[JZ] = -pos->tran.x*SB*CA + pos->tran.y*SA + (pos->tran.z)*CB*CA - Lz*CB*CA + Lz;

    joints[JA] = pos->a;
    joints[JB] = pos->b;
  } else {
    joints[0] = pos->tran.x;
    joints[1] = pos->tran.y;
    joints[2] = pos->tran.z;
    joints[3] = pos->a;
    joints[4] = pos->b;
  }

  return 0;
}

static int kinematicsInverse(const EmcPose * pos,
    double *joints,
    const KINEMATICS_INVERSE_FLAGS * iflags,
    KINEMATICS_FORWARD_FLAGS * fflags)
{

  kinematicsInverseFromState(current_state, pos, joints, iflags, fflags);

  return 0;
}

int kinematicsHome(EmcPose * world,
    double *joint,
    KINEMATICS_FORWARD_FLAGS * fflags,
    KINEMATICS_INVERSE_FLAGS * iflags)
{
  *fflags = 0;
  *iflags = 0;

  return kinematicsForward(joint, world, fflags, iflags);
}

KINEMATICS_TYPE kinematicsType(void)
{
  return KINEMATICS_BOTH;
}

#include "rtapi.h" /* RTAPI realtime OS API */
#include "rtapi_app.h" /* RTAPI realtime module decls */
#include "hal.h"

MODULE_LICENSE("GPL");

static vtkins_t vtk = {
  .kinematicsForward = kinematicsForward,
  .kinematicsInverse  = kinematicsInverse,
  .kinematicsHome = kinematicsHome,
  .kinematicsType = kinematicsType
};

static int comp_id, vtable_id;
static const char *name = "pocketnckins";

int rtapi_app_main(void)
{
  int res = 0;
  comp_id = hal_init(name);
  if (comp_id < 0) return comp_id;

  vtable_id = hal_export_vtable(name, VTVERSION, &vtk, comp_id);

  if (vtable_id < 0) {
    rtapi_print_msg(RTAPI_MSG_ERR,
        "%s: ERROR: hal_export_vtable(%s,%d,%p) failed: %d\n",
        name, name, VTVERSION, &vtk, vtable_id );
    return -ENOENT;
  }

  haldata = hal_malloc(sizeof(struct haldata));

  res = hal_pin_bit_new("pocketnckins.five-axis-kinematics", HAL_IN, &(haldata->five_axis_kinematics), comp_id);
  if(res < 0) goto error;

  res = hal_pin_float_new("pocketnckins.tool-z-offset", HAL_IN, &(haldata->tool_z_offset), comp_id);
  if(res < 0) goto error;

  res = hal_pin_bit_new("pocketnckins.carte-space-changed", HAL_OUT, &(haldata->carte_space_changed), comp_id);
  if(res < 0) goto error;

  res = hal_pin_bit_new("pocketnckins.carte-space-change-ok", HAL_IN, &(haldata->carte_space_change_ok), comp_id);
  if(res < 0) goto error;

  res = hal_pin_float_new("pocketnckins.pos-x", HAL_OUT, &(haldata->pos_x), comp_id);
  if(res < 0) goto error;

  res = hal_pin_float_new("pocketnckins.pos-y", HAL_OUT, &(haldata->pos_y), comp_id);
  if(res < 0) goto error;

  res = hal_pin_float_new("pocketnckins.pos-z", HAL_OUT, &(haldata->pos_z), comp_id);
  if(res < 0) goto error;

  hal_ready(comp_id);
  return 0;
error:
  hal_exit(comp_id);
  return res;
}

void rtapi_app_exit(void) {
  hal_exit(comp_id);
}
