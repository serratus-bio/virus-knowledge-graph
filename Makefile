setup: install env

install:
	{ \
	sudo yum install make ;\
	sudo yum install docker -y ;\
	sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)"  -o /usr/local/bin/docker-compose ;\
	sudo mv /usr/local/bin/docker-compose /usr/bin/docker-compose ;\
	sudo chmod +x /usr/bin/docker-compose ;\
	sudo chmod 666 /var/run/docker.sock ;\
	sudo systemctl start docker ;\
	}

mount-vol:
	{ \
	DEVICE_NAME=nvme1n1 ;\
	MOUNT_DIR=graphdata ;\
	mkdir -p /mnt/graphdata ;\
	mount /dev/nvme1n1 /mnt/graphdata -t ext4 ;\
	sudo chown `whoami` /mnt/graphdata/* ;\
	}

clean:
	docker system prune -a -f 

env-etl:
	printf '%s\n' 'NEO4J_USER=""' 'NEO4J_PASSWORD=""' 'NEO4J_URI=""' > ./jobs/etl/.env

run-etl-all:
	docker-compose up --build etl

clear-etl-cache:
	rm /mnt/graphdata/*.csv

connect-etl:
	docker exec -it $(docker ps -aqf "name=etl")  /bin/bash
