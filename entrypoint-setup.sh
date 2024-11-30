#!/bin/sh
python django/manage.py makemigrations auth graphql_auth
python django/manage.py migrate
python django/manage.py sync-schedulers
python django/manage.py import-initial-data
python django/manage.py synchronize-tasks
python django/manage.py collectstatic --noinput
