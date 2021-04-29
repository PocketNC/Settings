// eepromReadWPR.c can be compiled with gcc eepromReadWPR.c -o eepromReadWPR
// eeeprom.isLocked relies on eepromReadWPR executable being in the Settings folder
// Maybe this should be in a bin folder somewhere with a Makefile that can run
// in a postUpdate script to ensure programs that require compiling are compiled 
// when updated.

#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

int i2c_write_read(int handle,
                   unsigned char addr_w, unsigned char *buf_w, unsigned int len_w,
                   unsigned char addr_r, unsigned char *buf_r, unsigned int len_r) {
  struct i2c_rdwr_ioctl_data msgset;
  struct i2c_msg msgs[2];

  msgs[0].addr=addr_w;
  msgs[0].len=len_w;
  msgs[0].flags=0;
  msgs[0].buf=buf_w;

  msgs[1].addr=addr_r;
  msgs[1].len=len_r;
  msgs[1].flags=1;
  msgs[1].buf=buf_r;

  msgset.nmsgs=2;
  msgset.msgs=msgs;

  if (ioctl(handle,I2C_RDWR,(unsigned long)&msgset)<0) {
    fprintf(stderr, "i2c_write_read error: %s\n",strerror(errno));
    return -1;
  } 
  return(len_r);
}

int main(int argc, char** argv) {
  const char filename[] = "/dev/i2c-1";
  int file;

  if((file = open(filename, O_RDWR)) < 0) {
    printf("Failed to open the bus.\n");
    exit(1);
  }

  char configRegValue;
  char writeData[2] = { 0b10000000, 0x0 };
  char addr = 0x50;

  i2c_write_read(file, addr, writeData, 2, addr, &configRegValue, 1);

  printf("%d\n", configRegValue);

  return 0;
}

