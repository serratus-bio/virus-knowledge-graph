## Commands for machine setup

setup: install mount-vol env-etl env-ml docker-start

install:
	./machines/install.sh

mount-vol:
	./machines/mount-volume.sh

neo4j-backup:
	./machines/neo4j-backup.sh

neo4j-restore:
	./machines/neo4j-restore.sh

## Commands for jobs

docker-start:
	sudo service docker start && sudo chmod 666 /var/run/docker.sock

docker-clean:
	docker system prune -a -f

env-etl:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' > ./jobs/etl/.env

run-etl-all:
	docker-compose up --build etl

clear-etl-cache:
	rm /mnt/graphdata/*.csv

connect-etl:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash

env-ml:
	printf '%s\n' 'NEO4J_USER="neo4j"' 'NEO4J_PASSWORD=""' 'NEO4J_URI="bolt://:7687"' > ./jobs/graph_learning/.env
