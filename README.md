How to install pgAgent in the container with **Postgres**:

see 
https://karatejb.blogspot.com/2020/04/postgresql-pgagent-scheduling-agent.html

To go into a docker container with bash:

$ winpty docker exec -it -u=root scrape-mountain-weather-data-postgres //bin//sh

Then run 

$ apt-get update && apt-get install pgagent

Then, must go into pgAdmin and under the tree, expand the data base and click "Extensions".
Then, right click Create > Extension... and under Name type pgagent.
Then simply refresh and there should be a place for pgAgent Jobs at the bottom. 

Currently, the Dockerfile should be taking care of everything except the last part.