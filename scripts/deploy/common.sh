#!/bin/bash
cd "$(dirname "$0")"

export PROJECT_PATH="$(dirname $(dirname $(dirname $(realpath "$0"))))"

source "$PROJECT_PATH/.env"

export USER_ID="maintainers"
export GROUP_ID="maintainers"
export USER_HOME="/home/$USER_ID"
export PROJECT_NAME="${PROJECT_NAME}"
export SOURCE_DIRECTORY="$USER_HOME/$PROJECT_NAME/django"
export DEPLOY_SCRIPTS_PATH="$PROJECT_PATH/scripts/deploy"
export DEPLOY_SCRIPT_PATH="$DEPLOY_SCRIPTS_PATH/prod_deploy.sh"

export GITLAB_URL="gitlab.com"
export GITLAB_GROUP_NAME="cpj-ca/job-seekers"
export GIT_CLONE_REPOSITORIES=()
export SITE_URL="${SITE_URL}"
export PROJECT_GITLAB_HOOKS_URL="https://$GITLAB_URL/${GITLAB_GROUP_NAME}/$PROJECT_NAME/-/hooks"
export DEFAULT_GIT_BRANCH_NAME="master"

export TERMINAL_COLUMNS="$(stty -a 2>/dev/null | grep -Po '(?<=columns )\d+' || echo 0)"

export DATABASE_NAME="$DB_NAME"
export DATABASE_USER="$DB_USERNAME"
export DATABASE_DEFAULT_PASSWORD="$DB_PASSWORD"
export DATABASE_PASSWORD="${DATABASE_PASSWORD:-$DATABASE_DEFAULT_PASSWORD}"
export DATABASE_PORT="${DB_PORT:-5432}"

export WEBHOOK_PORT=9000
export WEBHOOK_URL="http://$SITE_URL:$WEBHOOK_PORT/hooks/$PROJECT_NAME"

export SUDOERS_FILE_NAME="$PROJECT_NAME"

export GUNICORN_BASE_NAME="${PROJECT_NAME}_gunicorn"
export CELERY_BASE_NAME="${PROJECT_NAME}_celery"
export SOCKET_DIRECTORY="$USER_HOME/run"
export SOCKET_FILE="$SOCKET_DIRECTORY/${PROJECT_NAME}_gunicorn.sock"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

function print_separator() {
    for ((i = 0; i < "$TERMINAL_COLUMNS"; i++)); do
        printf $1
    done
}

function echo_run() {
    line_count=$(wc -l <<<$1)
    echo -n ">$(if [ ! -z ${2+x} ]; then echo "($2)"; fi)_ $(sed -e '/^[[:space:]]*$/d' <<<$1 | head -1 | xargs)"
    if (($line_count > 1)); then
        echo -n "(command truncated....)"
    fi
    echo
    if [ -z ${2+x} ]; then
        eval $1
    else
        FUNCTIONS=$(declare -pf)
        echo "$FUNCTIONS; $1" | sudo --preserve-env -H -u $2 bash
    fi
    print_separator "+"
    echo -e "\n"
}

export IS_SCRIPT_END=false
function on_exit() {
    IS_SCRIPT_END=true
    exit 0
}
