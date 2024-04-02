#!/bin/bash

psql -U "$POSTGRES_USER" -W postgres -c "CREATE EXTENSION pgagent"