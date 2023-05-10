# Get device name from output
lsblk

DEVICE_NAME=nvme1n1
MOUNT_DIR=graphdata

file -s /dev/$DEVICE_NAME
mkdir -p /mnt/$MOUNT_DIR
sudo chown ec2-user /mnt/$MOUNT_DIR
mount /dev/$DEVICE_NAME /mnt/$MOUNT_DIR -t ext4
df -h /mnt/$MOUNT_DIR

# Automount EBS Volume on Reboot
cp /etc/fstab /etc/fstab.bak
grep -q "/mnt/$MOUNT_DIR" /etc/fstab || printf "UUID=/dev/$DEVICE_NAME /mnt/$MOUNT_DIR ext4 defaults,nofail 0 0" >> /etc/fstab
mount -a