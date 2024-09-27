#!/bin/bash

BACKUP_DIR=/mnt/graphdata/neo4j

if [[ !"$(sudo systemctl stop neo4j)" ]]; then
  while [[ "$(neo4j status)"]]; do
    sleep 1
    echo "Still waiting..."
  done
fi

# Backup to local directory
mkdir -p $BACKUP_DIR
[ -f $BACKUP_DIR/neo4j.dump ] && mv $BACKUP_DIR/neo4j.dump $BACKUP_DIR/neo4j.dump.old
sudo /bin/neo4j-admin database dump --to-path=$BACKUP_DIR --verbose neo4j

# Backup to s3 (TODO: use flag to determine if s3 backup is needed)
# timestamp=$(date +%Y%m%d-%H%M%S)
# aws s3 cp /mnt/graphdata/neo4j/neo4j.dump s3://serratus-graph/neo4j-backups/neo4j.dump.$timestamp

sudo systemctl start neo4j
