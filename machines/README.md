## Read vs. Write instances

The free Neo4j community edition (free version) doesn't support Role-based security or multiple access levels for a single server, this means we can only have either read-only and read-write access.
Moreover, the RAM requirements for running GDS graph algorithms and ML workloads is much higher and more expensive than a database only used for reading graph queries.

To workaround these limitations, we have two seperate instances:
  - `neo4j-graph-worker`: is a high-mem instance with write access, config settings and additional plugins to support ETL and ML workloads. This machine can be turned on only when it's needed for offline workloads.
  - `neo4j-graph-server`: is a t3-med instance with read-only access that is configured for serving data, it can be left running for web application use.

Both instances can synchronize by using [backup](./neo4j-backup.sh) and [restore](./neo4j-restore.sh) scripts, either from S3 or a shared EBS multi-attach storage. 

## Making updates to existing graph database

Warnings: 
- Read through the backup and restore scripts before running. Some lines may need to commented/uncommented depending on intended behaviour.
- This causes a ~5 min outage, since the restore step requries turning off the database

1. Turn on `neo4j-graph-worker` instance
1. Make updates to graph with [write user](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=Neo4j-Graph&region=us-east-1)
1. Run [backup script](./neo4j-backup.sh)  to create backup file
1. (Optional) upload backup to s3
1. Connect to `neo4j-graph-server` and run the [restore script](./neo4j-restore.sh)


## Initial worker machine and ETL Setup

If the `neo4j-graph-worker` is not already created, you can create the instance from scratch:

1. Create Neo4j CloudFormation stack 
   - Go to [cloudformation in AWS console](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filteringText=&filteringStatus=active&viewNested=true)
   - Click "Create stack" and select "With new resources"
   - Input S3 URL to latest cloudformation yaml template ([template](./cloudformation/neo4j-community.template.yaml), [existing s3 url](https://cf-templates-1cgp5cn7sjaka-us-east-1.s3.amazonaws.com/neo4j-community.template.yaml))
  - Choose name: neo4j-graph-worker
  - Choose password from [AWS secrets](https://us-east-1.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-1)
  - Choose Yes to include ML plugins
  - Choose instance type: t3.medium or t3.large or larger
  - Choose disk size: 50-100 GBs
  - Enter SSH CIDR: 0.0.0.0/0
  - Choose keyname pair: `neo4j` or personal ssh key
  - Add tag: project: openvirome
  - Add IAMRole: `AWSCloudformationFullAccessRole`
  - Leave other default settings
  - Submit and wait for completion (~10 mins)
  - Check "Outputs" tab to find URL
1. (Optional) If not already created, can create a shared EBS volume or s3 bucket for storing backups. 
   - EBS volume: 
      - Existing volume: `vol-0a228a503a868b12d`
      - Size: 100 GiB, Type: io1 (supports Multi-attach), IOPS: 1600+, Enable Multi-attach
   - S3 Bucket:
      - [serratus-graph](https://us-east-1.console.aws.amazon.com/s3/buckets/serratus-graph?region=us-east-1&bucketType=general&prefix=neo4j-backups/&showversions=false)
1. Connect to instance using selected ssh key (`neo4j.pem`) or EC2 Instance Connect.
1. Install git and clone repo on machine
   - `sudo yum update -y && sudo yum install git -y && sudo yum install make`
   - `mkdir workspace && cd workspace && git clone https://github.com/serratus-bio/virus-knowledge-graph && cd virus-knowledge-graph`
1. Run `make install` and `make mount-vol` to mount volume to `/mnt/graphdata`
1. Restore data (if backup already available) 
   - `make neo4j-restore`
1. Or run full ETL job to populate db from scratch
   - set up .env then `make etl-run`
1. Create a new backup after changes are made
   - `make neo4j-backup`

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


### CloudFormation Infrastructure

[Template](./cloudformation/neo4j-community.template.yaml)

[Reference](https://github.com/neo4j-partners/amazon-cloud-formation-neo4j)

![DB node stack](./cloudformation/aws-community.png)
