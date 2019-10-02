#!/bin/sh
cd "$(dirname "$(dirname "$0")")"
PROJ="$(basename "$(pwd)")"
docker run -ti --rm --network ${PROJ}_default -v $PWD/scripts:/scripts -v $PWD/volumes/dataset-cache:/dataset_cache -e ELASTICSEARCH_HOSTS=elasticsearch:9200 -e LAZO_SERVER_HOST=lazo_server -e LAZO_SERVER_PORT=50051 ${PROJ}_coordinator python /scripts/purge_source.py "$1"
