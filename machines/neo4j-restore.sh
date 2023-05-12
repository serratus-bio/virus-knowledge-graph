#!/bin/bash

# Restore
/bin/neo4j-admin database load --from-path=/mnt/graphdata/neo4j/neo4j.dump neo4j --overwrite-destination=true
neo4j start
