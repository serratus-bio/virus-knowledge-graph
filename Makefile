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

## Docker

docker-start:
	sudo service docker start && sudo chmod 666 /var/run/docker.sock

docker-clean:
	docker system prune -a -f

### ETL

etl-env:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' 'PYTHONUNBUFFERED=1' > ./jobs/etl/.env

etl-run:
	docker-compose up --build etl

etl-clear-cache:
	rm /mnt/graphdata/*.csv

etl-connect:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash

### ML

ml-env:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' 'PYTHONUNBUFFERED=1' > ./jobs/graph_learning/.env

ml-run:
	docker-compose up --build graph_learning

ml-connect:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash

