#!/bin/bash
# Create directories that PostgresQL needs to function. Because these
# directories are empty, they are not tracked by version control (i.e. Git) and
# therefore are not part of the GitHub repo.
# see also https://stackoverflow.com/questions/70464894/postgres-empty-directories-and-github

# NOTE: so far this script is untested, use at your own risk

for n in pg_commit_ts pg_dynshmem pg_notify pg_replslot pg_serial pg_snapshots pg_stat pg_tblspc pg_twophase pg_logical/mappings pg_logical/snapshots pg_wal/archive_status;
  do
    if [ ! -d ../data/postgres_data/$n ]
      then
        echo "Creating directory ../data/postgres_data/$n"
        mkdir "../data/postgres_data/$n"
    fi
  done
