Note: if you are cloning this repo, run create_postgres_directories.sh using BASH before doing anything else. 
This is needed because PostgresQL requires the presence of some empty directories under postgres_data, and because 
they are empty they are not captured by Git. 

Note that I admittedly haven't really tested this, but running it should at least ensure that the same file 
structure under postgres_data is recapitulated. 

Using BASH, navigate to orca-data-to-db/orca-data-to-db/src/ directory. 
Then, run the command "docker compose --env-file dev.env up", which will start the Docker 
containers for Mage, PostgreSQL, and pgAdmin.

Mage can be accessed from localhost:6789. Running the pipeline fore_to_postgres will scrape
current weather data from the given mountains and elevations on mountain-forecast.com and put the resulting 
data in Postgres.

The data in Postgres can be accessed via pgAdmin from localhost:8080. The data is at first put into
a "staging" table, and then consolidated into a "final" table containing only one set of records to each
"time issued" from mountain-forecast.com. These processes should be run automatically via pgAgent; if 
needed, they can be run as manual queries by the user. These queries can be found in sql_queries_backup.txt.


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

Then, must go into pgAdmin and under the tree, expand the data base and click "Extensions".
Then, right click Create > Extension... and under Name type pgagent.
Then simply refresh and there should be a place for pgAgent Jobs at the bottom. 
Make sure you see 'pgagent' and 'plpgsql' under Extensions as well.

Currently, the Dockerfile should be taking care of everything except the last part.