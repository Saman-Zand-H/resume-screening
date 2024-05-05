#!/bin/sh
python django/manage.py makemigrations auth graphql_auth
python django/manage.py migrate
python django/manage.py collectstatic --noinput

if [ "$1" = "pubsub" ]; then
    python django/manage.py run_sub
else
    cd django
    gunicorn config.asgi:application --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker --workers $(($(nproc) * 2 + 1)) --threads 2 --timeout 120 --log-level info
fi
