FROM python:3.5.3-alpine
WORKDIR /usr/src/app
ARG FLASK_APP

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    postgresql-dev \
    git \
  && pip install --upgrade pip \
  && pip install pipenv gunicorn json-logging-py pudb

# Configure "pudb" debugger not to show a welcome screen.
RUN sed 's/seen_welcome = a/seen_welcome = e034/g' ~/.config/pudb/pudb.cfg -i

# Install the required packages, copy the app.
ENV FLASK_APP=$FLASK_APP
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv install --deploy --system
COPY . .
RUN python -m compileall .

# Ensure flask is not bugged by an .env file.
RUN rm .env

# Configure alembic to use JSON logging.
RUN docker_flask/set_json_log_handler.py migrations/alembic.ini

# Compile translation (.po) files if necessary.
RUN ! which pybabel || pybabel compile -d $FLASK_APP/translations

ENTRYPOINT ["/usr/src/app/docker_flask/entrypoint.sh"]
CMD ["serve"]

################################################################################

# This sets the desired granularity of log outputs. Valid level names
# are: debug, info, warning, error, critical
ENV GUNICORN_LOGLEVEL=warning

# This sets the type of workers to use with gunicorn.
ENV GUNICORN_WORKER_CLASS=sync

# This sets the number of worker processes for handling requests -- a
# positive integer generally in the 2-4 * $NUM_CORES range.
ENV GUNICORN_WORKERS=2

# This sets the number of worker threads for handling requests. (Runs
# each worker with the specified number of threads.) Only affects the
# "gthread" and "sync" worker types.
ENV GUNICORN_THREADS=1
