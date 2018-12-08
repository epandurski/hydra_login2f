#!/bin/sh
set -e

logging_conf='/usr/src/app/docker_flask/logging.conf'
gunicorn_conf='/usr/src/app/docker_flask/gunicorn.conf'

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/usr/src/app
case $1 in
    develop)
        shift;
        export FLASK_ENV=development
        exec flask run --host=0.0.0.0 --port $PORT "$@"
        ;;
    debug)
        shift;
        export FLASK_ENV=development
        exec python -u wsgi.py "$@"
        ;;
    serve)
        exec gunicorn --config "$gunicorn_conf" --log-config "$logging_conf" -b :$PORT wsgi:app
        ;;
    upgrade-schema)
        shift;
        exec flask db upgrade "$@"
        ;;
    db)
        shift;
        exec flask db "$@"
        ;;
    signalbus)
        shift;
        exec flask signalbus "$@"
        ;;
    supervisord)
        exec supervisord -c /usr/src/app/docker_flask/supervisord.conf
        ;;
    *)
        exec "$@"
        ;;
esac
