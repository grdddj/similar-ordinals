#!/bin/sh

set -e

# Check if the lock file exists, if it does, exit
lock_file="/tmp/update_and_restart.sh.lock"
if [ -e "${lock_file}" ]; then
    echo "Script is already running. Exiting."
    exit 1
fi
touch "${lock_file}"
cleanup() {
    echo "Cleaning up"
    rm -f "${lock_file}"
}
trap cleanup EXIT

cd "$(dirname "$0")"

./status.sh

echo "starting update_data.py"
python3.8 update_data.py

./status.sh

echo "restart backup API"
./restart_backup_api.sh

./status.sh

echo "sleeping 10 seconds"
sleep 10

echo "restarting main API"
./restart_api.sh

sleep 1

./status.sh

echo "finished restarting"
