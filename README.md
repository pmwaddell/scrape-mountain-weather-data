Note: if you are cloning this repo, run create_postgres_directories.sh using BASH before doing anything else. 
This is needed because PostgresQL requires the presence of some empty directories under postgres_data, and because 
they are empty they are not captured by Git. As of 4/2/24, I no longer track the postgres_data directory
with git, so this may no longer be necessary.

Note that I admittedly haven't really tested this, but running it should at least ensure that the same file 
structure under postgres_data is recapitulated. 

Using BASH, navigate to orca-data-to-db/orca-data-to-db/src/ directory. 
Then, run the command "docker compose --env-file dev.env up", which will start the Docker 
containers for Mage, PostgreSQL, and pgAdmin.

Mage can be accessed from localhost:6789. Running the pipeline fore_to_postgres will scrape
current weather data from the given mountains and elevations on mountain-forecast.com and put the resulting 
data in Postgres. You may need to edit the loader of this pipeline to create the table forecast_data.scraped_
forecasts_final and populate it with initial data, if it doesn't already exist.


The data in Postgres can be accessed via pgAdmin from localhost:8080. The data is at first put into
a "staging" table, and then consolidated into a "final" table containing only one set of records to each
"time issued" from mountain-forecast.com. Data from the "staging" table is accumulated from each scrape 
until it is 3 days old, at which point it is dropped. 

This upserting and dropping should be run automatically via pgAgent (see the tab for pgAgent Jobs at the bottom); 
if needed, they can be run as manual queries by the user. These queries can be found in sql_queries_backup.txt.

Note that when the scraped_forecasts_final table is first created, it needs to have the columns mtn_name, 
elevation, local_time_issued and local_time_of_forecast set as primary keys. The command for this can also be found
in sql_queries_backup.txt. Note also that if Autocommit is off, you may need to add COMMIT; after these queries.

The pipelines postgres_f_to_csv (for the "final" forecast table), postgres_s_to_csv (for the "staging" forecast table) 
and csv_to_postgres can be used to save the data in Postgres to a local .csv file
found in src/forecast_data, and to load the data from a .csv file in src/forecast_data back into Postgres (under a 
Schema called loaded_backups) respectively.

To send data to BQ, you need to set up a GCP account and project. Then go into the project and set up a 
Service Account as project owner. Create a Key for this account, download it and place it into the directory
designated folder in docker-compose.yaml (/Documents/secrets/personal-gcp.json by default seems to work).

_How to install pgAgent in the container with **Postgres**:_

see 
https://karatejb.blogspot.com/2020/04/postgresql-pgagent-scheduling-agent.html

and also
https://www.ibm.com/docs/en/z-chatops/1.1.4.x?topic=software-installing-pgagent

To go into a docker container with bash:

$ winpty docker exec -it -u=root scrape-mountain-weather-data-postgres //bin//sh

Then run 

$ apt-get update && apt-get install pgagent

Next, you must connect pgAgent to the Postgres database, which can be done with the command:

$ usr/bin/pgagent hostaddr=127.0.0.1 port=5432 dbname=postgres user=${POSTGRES_USER} password=${POSTGRES_PASSWORD}

The connection can be checked by 

$ ps -ef |grep pgagent

But you may need to install procps if this doesn't work first:

$ apt-get update && apt-get install procps

Then, must go into pgAdmin and under the tree, expand the data base and click "Extensions".
Then, right click Create > Extension... and under Name type pgagent.
Then simply refresh and there should be a place for pgAgent Jobs at the bottom. 
Make sure you see 'pgagent' and 'plpgsql' under Extensions as well.

Currently, the Dockerfile should be taking care of everything except the last part. 
However, it seems that the user may still need to manually go into the Docker container
and restart pgAgent when firing it back up.