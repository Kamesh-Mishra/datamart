#!/bin/bash

set -eu
set -o pipefail

if [ "x${DOCKER_HOST-}" = x ]; then
    echo "DOCKER_HOST is not set; you should run 'eval \$(minikube docker-env)" >&2
    exit 1
fi

DOCKER_HOST= sudo -g docker docker save busybox docker.elastic.co/elasticsearch/elasticsearch:6.4.3 remram/rabbitmq:3.7.8 datamart_coordinator datamart_query datamart_profiler datamart_example_discoverer \
    | docker load
