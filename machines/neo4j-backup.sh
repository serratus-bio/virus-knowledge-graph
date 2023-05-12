#!/bin/bash

BACKUP_DIR=/mnt/graphdata/neo4j

if [[! "${sudo systemctl stop neo4j}"]]; then
  while [["${neo4j status}"]];
    sleep 1
    echo "Still waiting..."
  done;
fi

mkdir -p $BACKUP_DIR
sudo /bin/neo4j-admin database dump --to-path=$BACKUP_DIR --verbose neo4j
sudo systemctl start neo4j
