#!/bin/sh
python django/manage.py makemigrations auth graphql_auth
python django/manage.py migrate
python django/manage.py collectstatic --noinput
if [ "$1" = "pubsub" ]; then
    python django/manage.py run_sub
else
    python django/manage.py runserver 0.0.0.0:8000 --insecure
fi