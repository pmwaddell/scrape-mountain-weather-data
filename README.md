How to install pgAgent in the container with pgAdmin:

see 
https://karatejb.blogspot.com/2020/04/postgresql-pgagent-scheduling-agent.html
and
https://stackoverflow.com/questions/48001082/oci-runtime-exec-failed-exec-failed-executable-file-not-found-in-path

To go into a docker container with bash:

$ winpty docker exec -it -u=root src-pgadmin-1 //bin//sh

Since the image is running Alpine Linux, we need to use apk instead of apt-get: 

$ apk update && apk add pgagent

Then, must go into Query tool in pgAdmin and execute:

CREATE EXTENSION pgagent IF NOT EXISTS;
CREATE LANGUAGE plpgsql IF NOT EXISTS;
