#!/bin/bash

DEVICE_NAME=nvme1n1
MOUNT_DIR=/mnt/graphdata

# Mount EBS Volume
mkdir -p $MOUNT_DIR
sudo chown `whoami` $MOUNT_DIR
sudo mount /dev/$DEVICE_NAME $MOUNT_DIR -t ext4

# Automount EBS Volume on Reboot
cp /etc/fstab /etc/fstab.bak
grep -q "$MOUNT_DIR" /etc/fstab || printf "UUID=$(sudo blkid -s UUID -o value /dev/nvme1n1) $MOUNT_DIR ext4 defaults,nofail 0 0" >> /etc/fstab
mount -a
