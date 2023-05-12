#!/bin/bash

############################
## Useful debugging commands
## Get device name from output
# lsblk
## Get filesystem type
# file -s /dev/$DEVICE_NAME
## Get memory usage
# df -h /mnt/$MOUNT_DIR
############################

DEVICE_NAME=nvme1n1
MOUNT_DIR=graphdata

# Mount EBS Volume
mkdir -p /mnt/$MOUNT_DIR
sudo chown `whoami`  /mnt/$MOUNT_DIR
mount /dev/$DEVICE_NAME /mnt/$MOUNT_DIR -t ext4

# Automount EBS Volume on Reboot
cp /etc/fstab /etc/fstab.bak
grep -q "/mnt/$MOUNT_DIR" /etc/fstab || printf "UUID=/dev/$DEVICE_NAME /mnt/$MOUNT_DIR ext4 defaults,nofail 0 0" >> /etc/fstab
mount -a
