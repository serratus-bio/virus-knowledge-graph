#!/bin/bash

DEVICE_NAME=nvme1n1
MOUNT_DIR=/mnt/graphdata

# Mount EBS Volume
mkdir -p $MOUNT_DIR
sudo chown ec2-user $MOUNT_DIR
sudo chgrp ec2-user $MOUNT_DIR

## Only run the following if the volume is not already formatted
## Otherwise data will be lost
# sudo mkfs -t ext4 /dev/$DEVICE_NAME
sudo mount /dev/$DEVICE_NAME $MOUNT_DIR

# Automount EBS Volume on Reboot
cp /etc/fstab /etc/fstab.bak
grep -q "$MOUNT_DIR" /etc/fstab || printf "UUID=$(sudo blkid -s UUID -o value /dev/$DEVICE_NAME) $MOUNT_DIR ext4 defaults,nofail 0 0" | tee -a /etc/fstab
mount -a
