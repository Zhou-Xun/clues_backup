#!/bin/bash 

dockerimage=$(docker images testing-docker -q)

docker rmi -f $dockerimage
docker build -t testing-docker .

newdockerimage=$(docker images testing-docker -q)
docker tag $newdockerimage 229471331279.dkr.ecr.us-east-2.amazonaws.com/testing-docker-search
docker push 229471331279.dkr.ecr.us-east-2.amazonaws.com/testing-docker-search

# if on windows, you can download spd-say to get an audio notif when this script finishes
# on mac you can change command to "say 'boom'"
# spd-say "boom"