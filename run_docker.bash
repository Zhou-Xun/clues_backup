#!/bin/bash 

dockerimage=$(docker images pyterrier-search -q)

docker rmi -f $dockerimage
docker build -t pyterrier-search .

newdockerimage=$(docker images pyterrier-search -q)
docker tag $newdockerimage 229471331279.dkr.ecr.us-east-2.amazonaws.com/pyterrier-search
docker push 229471331279.dkr.ecr.us-east-2.amazonaws.com/pyterrier-search

# if on windows, you can download spd-say to get an audio notif when this script finishes
# on mac you can change command to "say 'boom'"
spd-say "boom"