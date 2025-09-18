#!/bin/bash

set -o errexit
set -o pipefail

source /app/.venv/bin/activate

# Logging function
function log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Apply django migrations
function migrate(){
  log "Running migrations"
  python manage.py migrate
}

function collect_static() {
  log "copying all static files"
  python manage.py collectstatic --no-input
}

function ensuresuperuser() {
  log "Creating superuser"
  python manage.py ensuresuperuser
}

function setup() {
  log "Executing setup scripts"
  migrate
  collect_static
  ensuresuperuser
}

function run_server() {
  log "Running django server"
  python manage.py runserver 0.0.0.0:8080 --noreload
}

function run_wsgi() {
  log "Running wsgi server"
  gunicorn --bind 0.0.0.0:8080 backend.wsgi:application
}

function run_asgi() {
  log "Running asgi server"
  hypercorn --bind 0.0.0.0:8080 backend.asgi:application
}

function run_celery_worker() {
  log "Running celery worker"
  celery -A backend.celery worker --loglevel=INFO --pool=gevent --concurrency=4 --logfile=/dev/stdout
}

functions=("migrate" "collect_static" "ensuresuperuser" "setup" "run_server" "run_wsgi" "run_asgi" "run_celery_worker")

source /app/.venv/bin/activate
if [[ "${functions[*]}" =~ (^|[[:space:]])"$1"($|[[:space:]]) ]]; then
  "$1"
elif [ -z "${1}" ]; then
  setup
  run_asgi
else
  "$@"
fi
