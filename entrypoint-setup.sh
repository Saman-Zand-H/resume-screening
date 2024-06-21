#!/bin/sh
python django/manage.py makemigrations auth graphql_auth
python django/manage.py loaddata django/fixtures/ai.json
python django/manage.py migrate
python django/manage.py collectstatic --noinput
