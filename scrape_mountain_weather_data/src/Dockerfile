FROM mageai/mageai:latest

ARG USER_CODE_PATH=/home/src/${PROJECT_NAME}

# Note: this overwrites the requirements.txt file in your new project on first run.
# You can delete this line for the second run :)
COPY requirements.txt ${USER_CODE_PATH}requirements.txt

RUN pip3 install -r ${USER_CODE_PATH}requirements.txt


FROM postgres:14

RUN apt-get update && apt-get install pgagent && apt-get install procps

# Connect pgAgent to the Postgres database:
RUN usr/bin/pgagent hostaddr=127.0.0.1 port=5432 dbname=postgres user=${POSTGRES_USER} password=${POSTGRES_PASSWORD}