#!/bin/bash

# Backup
neo4j stop
/bin/neo4j-admin database dump --to-path=/mnt/graphdata/neo4j --verbose neo4j
