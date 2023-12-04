#!/bin/bash

BACKUP_DIR=/mnt/graphdata/neo4j

if [[! "${sudo systemctl stop neo4j}"]]; then
  while [["${neo4j status}"]];
    sleep 1
    echo "Still waiting..."
  done;
fi

sudo -u neo4j /bin/neo4j-admin database load --from-path=$BACKUP_DIR neo4j --overwrite-destination=true
sudo systemctl start neo4j
