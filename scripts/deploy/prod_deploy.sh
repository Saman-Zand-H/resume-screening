#!/bin/bash
cd "$(dirname "$0")"
source ./common.sh

VENV_PATH=$PROJECT_PATH/venv
DJANGO_PATH=$PROJECT_PATH/django
MANAGE_PATH=$DJANGO_PATH/manage.py

echo_log() {
    echo -e "$1"
}

echo_new_line() {
    echo -e "\n\n"
}

trap cleanup EXIT
function cleanup {
    exec &>/dev/null
}

git log -1 --pretty=format:'[%ai #%h] %an, %ae: %s'
echo_new_line

echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"
echo

echo_log ">_ source $VENV_PATH/bin/activate"
source $VENV_PATH/bin/activate

echo_log ">_ pip install -r $PROJECT_PATH/requirements.txt"
pip install -r $PROJECT_PATH/requirements.txt
echo_new_line

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
echo_log ">_ python3 $MANAGE_PATH collectstatic --noinput"
python3 $MANAGE_PATH collectstatic --noinput
echo_new_line
# echo_log ">_ python3 $MANAGE_PATH compilemessages"
# python3 $MANAGE_PATH compilemessages
echo_new_line
echo_log ">_ python3 $MANAGE_PATH makemigrations auth graphql_auth"
python3 $MANAGE_PATH makemigrations auth graphql_auth
echo_new_line
echo_log ">_ python3 $MANAGE_PATH migrate"
python3 $MANAGE_PATH migrate
echo_new_line

echo_log ">_ sudo systemctl restart $GUNICORN_BASE_NAME.service"
sudo systemctl restart $GUNICORN_BASE_NAME.service
