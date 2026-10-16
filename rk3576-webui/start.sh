#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -f server.pid ] && kill -0 "$(cat server.pid)" 2>/dev/null; then
    echo "Application is already running, PID $(cat server.pid)"
    exit 0
fi
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
export PYTHONUNBUFFERED=1
nohup /home/seeed/venvs/rknn-lite2-test/bin/python -B server.py >>server.log 2>&1 </dev/null &
echo $! >server.pid
echo "Started Edge Vision, PID $(cat server.pid), port ${PORT:-8080}"
