FROM python:3.9-alpine3.13
LABEL maintainer="Vu Ho <vuho.tech@gmail.com>"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    # Install postgresql-client package required for psycopg2 to connect to Postgres DB
    # Install jpeg-dev package required for running Pillow to hangle image uploading
    apk add --update --no-cache postgresql-client jpeg-dev && \
    # Install additional dependencies to build psycopg2 from source
    # Install additional dependencies (zlib, zlib-dev) for Pillow installation
    # These packages are only required for installation
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    # Shell command to check if the dev environment variable is true
    if [ $DEV = "true" ]; \
        # Install the dev dependencies
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    # Remove additional packages required for psycopg2 installation
    rm -rf .tmp-build-deps && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    # Assign ownership to django-user for the vol directory
    chown -R django-user:django-user /vol && \
    # Change the permissions (write for owner only, read and execute for everyone)
    # of all of the files within the vol directory
    chmod -R 755 /vol

ENV PATH="/py/bin:$PATH"

USER django-user