## Machine Setup

Aside from deploying the cloudformation resources, some manual actions are needed to set up the machine.

1. Create CloudFormation stack using [template](./cloudformation/neo4j-community.template.yaml).
1. Copy created EC2 instance id and stop instance.
1. Create EBS volume if not already created and associate to previously created EC2 instance.
   - Size: 100 GiB, Type: io1 (supports Multi-attach), IOPS: 1600+, Enable Multi-attach
1. Start instance, then connect to it using ssh key (`neo4j.pem`) or EC2 Instance Connect.
1. Install git and clone repo on machine
   - `sudo yum update -y && sudo yum install git -y`
   - `mkdir workspace && cd workspace && git clone https://github.com/serratus-bio/virus-host-graph && cd virus-host-graph`
1. Run `make install` and `make mount-vol` to mount volume to `/mnt/graphdata`
1. Restore data (if backup already on disk) or run full ETL job
   - `make restore`
   - OR: set up .env and run `make etl-run`


### Memory management

- Useful debugging commands for mounting volumes
   - Get device name from output: `lsblk`
   - Get filesystem and UID of device: `file -s /dev/$DEVICE_NAME`
   - Get memory usage: `df -h /mnt/$MOUNT_DIR`
   - Unmount device: `sudo umount /dev/$DEVICE_NAME`
   - System logs: `tail dmesg` or `journalctl -f`

### Manual Neo4j DB config management

- Ideally, use cloudformation to make changes to neo4j config. Alternatively, ssh into host, edit config and restart server.
- Useful commands neo4j server managment: 
   - Edit config file: `/etc/neo4j/neo4j.conf`
   - Download plugins: `/var/lib/neo4j/plugins`
   - Check status: `neo4j status`, `sudo service neo4j status` or `curl http://localhost:7474/`
   - Rveiw log files: `/var/log/neo4j/`
   - Restart instance: `neo4j stop && neo4j start` or `sudo service neo4j restart`
