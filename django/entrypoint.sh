#!/bin/sh

python manage.py migrate
python manage.py collectstatic --noinput
if [ "$1" = "pubsub" ]; then
    python manage.py run_sub
else
    python manage.py runserver 0.0.0.0:8000 --insecure
fi