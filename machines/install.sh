#!/bin/bash

yum check-update
sudo yum install make
sudo yum install docker -y
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)"  -o /usr/local/bin/docker-compose
sudo mv /usr/local/bin/docker-compose /usr/bin/docker-compose
sudo chmod +x /usr/bin/docker-compose
sudo chmod 666 /var/run/docker.sock
sudo systemctl start docker
