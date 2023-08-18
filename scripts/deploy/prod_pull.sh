#!/bin/bash
cd "$(dirname "$0")"
source ./common.sh

branch_name="$(sudo -u $USER_ID git -C $PROJECT_PATH rev-parse --abbrev-ref HEAD)"

sudo -u $USER_ID git -C $PROJECT_PATH reset --hard origin/$branch_name || exit
sudo -u $USER_ID git -C $PROJECT_PATH checkout --force $branch_name || exit
sudo -u $USER_ID git -C $PROJECT_PATH fetch -pP --tags --force || exit
sudo -u $USER_ID git -C $PROJECT_PATH pull origin $(cut -d'/' -f3 <<<$branch_name) || exit

chown -R $USER_ID:$GROUP_ID $USER_HOME

sudo -u $USER_ID DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE bash $DEPLOY_SCRIPT_PATH
