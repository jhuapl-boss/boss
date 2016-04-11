#!/bin/bash

# This script is run by Jenkins and is assumed to be invoked from the root
# folder of the repo.

# settings.py disables some dependencies when this env variable is set.
export USING_DJANGO_TESTRUNNER=1
export DJANGO_SETTINGS_MODULE=boss.settings.jenkins

# Start local DynamoDB.
java -Djava.library.path=/usr/local/bin/dynamo/DynamoDBLocal_lib/ -jar /usr/local/bin/dynamo/DynamoDBLocal.jar -inMemory &

# Ensure a fresh DB available.
mysql -u root --password=MICrONS < jenkins_files/fresh_db.sql

cd django

# Ensure migrations generated for a clean slate.
rm -rf */migrations

python3 manage.py makemigrations --noinput

# Force create migrations for the bosscore app.
python3 manage.py makemigrations bosscore --noinput

python3 manage.py migrate

python3 manage.py collectstatic --noinput

# Run tests.
python3 manage.py jenkins --enable-coverage --noinput

# Shutdown local DynamoDB.
kill $!
