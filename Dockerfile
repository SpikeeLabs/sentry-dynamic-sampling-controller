# base image
FROM python:3.10-slim as python-base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VENV_PATH="/app/venv" \
    APP_PATH="/app"
# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR $APP_PATH

RUN useradd -ms /bin/bash sentry \
    && apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Build
FROM python-base as builder-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# get poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$VENV_PATH"

ENV PATH="${PATH}:/root/.local/bin"


COPY pyproject.toml poetry.lock ./

RUN poetry export -f requirements.txt | "$VENV_PATH/bin/pip" install -r /dev/stdin

COPY . .

RUN poetry build && "$VENV_PATH/bin/pip" install dist/*.whl \
    && rm -rf dist/


# Static base
FROM builder-base as static-base

RUN python manage.py download_vendor_files && python manage.py collectstatic

# Static
FROM nginxinc/nginx-unprivileged:mainline-alpine as static
COPY --from=static-base /app/assets /usr/share/nginx/html

# Prod
FROM python-base as production
COPY --from=builder-base $APP_PATH $APP_PATH

RUN chmod u+rwx "$APP_PATH/manage.py"

USER sentry

CMD ["gunicorn", "controller.wsgi", "-c", "/app/config.py"]
