#!/bin/sh
python django/manage.py makemigrations auth graphql_auth
python django/manage.py migrate
python django/manage.py collectstatic --noinput

if [ "$1" = "pubsub" ]; then
    python django/manage.py run_sub
else
    gunicorn --chdir django config.asgi:application --bind :$PORT --worker-class uvicorn.workers.UvicornWorker --workers $(($(nproc) * 2 + 1)) --threads 2 --timeout 120 --log-level info
fi
