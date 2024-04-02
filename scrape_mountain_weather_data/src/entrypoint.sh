#!/bin/bash

# Start the agent process


/usr/bin/pgagent dbname=postgres user="$POSTGRES_USER"
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start first process: pg_agent: $status"
  exit $status
fi

# Start the second process
/entrypoint.sh "$@"
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start second process: postgres engine: $status"
  exit $status
fi

# The container exits with an error
# if it detects that either of the processes has exited.
# Otherwise it loops forever, waking up every 60 secons

while sleep 60; do
  ps aux |grep pgagent |grep -q -v grep
  PROCESS_1_STATUS=$?
  ps aux |grep postgres |grep -q -v grep
  PROCESS_2_STATUS=$?
  # If the greps above find anything, they exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    exit 1
  fi
done