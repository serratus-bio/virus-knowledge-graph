#!/bin/bash

BACKUP_DIR=/mnt/graphdata/neo4j


if [[ ! "$(sudo systemctl stop neo4j)" ]]; then
  while [[ "$(neo4j status)" ]]; do
    sleep 1
    echo "Still waiting..."
  done
fi

# Restore from local backup
sudo -u neo4j /bin/neo4j-admin database load --from-path=$BACKUP_DIR neo4j --overwrite-destination=true
sudo systemctl start neo4j


# Restore from s3 backup (TODO: run using flags, might need to remove suffix)
# S3_BACKUP_DIR=s3://serratus-graph/neo4j-backups
# S3_BACKUP_SUFFIX='20240927-144446'
## replace neo4j.dump with file copied from s3
# aws s3 cp $S3_BACKUP_DIR/neo4j.dump.$S3_BACKUP_SUFFIX $BACKUP_DIR/neo4j.dump
# sudo -u neo4j /bin/neo4j-admin database load --from-path=$BACKUP_DIR neo4j --overwrite-destination=true
# sudo systemctl start neo4j
