#!/bin/sh
if [ "$1" = "pubsub" ]; then
    python django/manage.py run_sub
else
    gunicorn --chdir django config.wsgi:application --bind :$PORT --workers $(($(nproc) * 2 + 1)) --threads 2 --timeout 120 --log-level info
fi
