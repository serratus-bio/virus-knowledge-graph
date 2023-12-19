## Machine

setup: install mount-vol env-etl env-ml docker-start

install:
	./machines/install.sh

mount-vol:
	./machines/mount-volume.sh

neo4j-backup:
	./machines/neo4j-backup.sh

neo4j-restore:
	./machines/neo4j-restore.sh

## Neo4j

neo4j-stop:
	sudo systemctl stop neo4j

neo4j-start:
	sudo systemctl start neo4j

neo4j-restart: neo4j-stop neo4j-start

neo4j-logs:
	tail -f  /var/log/neo4j/neo4j.log

neo4j-check-consitency:
	sudo /bin/neo4j-admin database check neo4j

neo4j-check-memory:
	du -hc /var/lib/neo4j/data/databases/neo4j/*store.db* | tail -n 1

## Docker

docker-start:
	sudo service docker start && sudo chmod 666 /var/run/docker.sock

docker-clean:
	docker system prune -a -f

### ETL container

etl-env:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' 'PYTHONUNBUFFERED=1' > ./jobs/etl/.env

etl:
	docker-compose up --build etl

etl-sql:
	WORKFLOW="sql_to_graph" docker-compose -p etl-sql up --build etl

etl-projection:
	WORKFLOW="graph_to_projection" docker-compose -p etl-projection  up --build etl

etl-clear-cache:
	rm /mnt/graphdata/*.csv

etl-connect:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash

### Graph learning container

ml-env:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' 'PYTHONUNBUFFERED=1' 'GRAPHISTRY_USERNAME="" GRAPHISTRY_PASSWORD=""' > ./jobs/graph_learning/.env

ml:
	docker-compose up --build graph_learning

ml-connect:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash

ml-dataset:
	WORKFLOW="make_datasets" docker-compose -p ml-dataset up --build graph_learning

lp-pyg:
	WORKFLOW="link_prediction_pyg" docker-compose -p lp-pyg up --build graph_learning

lp-gds:
	WORKFLOW="link_prediction_gds" docker-compose -p lp-gds up --build graph_learning

lp-nx:
	WORKFLOW="link_prediction_nx" docker-compose -p lp-nx up --build graph_learning
