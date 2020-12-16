#!/bin/bash

set -e

# Check if the database is available
if [ -z "$SKIP_BROKER_CHECK" -o "$SKIP_BROKER_CHECK" = "0" ]; then
    wait-for-it.sh -t 20 "${BROKER_HOST}:${BROKER_PORT-5672}"
fi

# Start server
if [[ ! -z "$@" ]]; then
    echo "Command is $@"
    "$@"
elif [[ "$DEV_SERVER" = "1" ]]; then
    uvicorn poster.main:app --host 0.0.0.0 --reload
else
    gunicorn poster.main:app --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
fi
