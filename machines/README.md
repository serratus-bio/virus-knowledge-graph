## Setup

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
   - OR: set up .env and run `make run-etl-all`
