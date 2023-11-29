#!/bin/bash

BACKUP_DIR=/mnt/graphdata/neo4j

if [[! "${sudo systemctl stop neo4j}"]]; then
  while [["${neo4j status}"]];
    sleep 1
    echo "Still waiting..."
  done;
fi

mkdir -p $BACKUP_DIR
[ -f $BACKUP_DIR/neo4j.dump ] && mv $BACKUP_DIR/neo4j.dump $BACKUP_DIR/neo4j.dump.old
sudo -u neo4j /bin/neo4j-admin database dump --to-path=$BACKUP_DIR --verbose neo4j
[ -f $BACKUP_DIR/neo4j.dump ] && rm -f $BACKUP_DIR/neo4j.dump.old

sudo systemctl start neo4j
