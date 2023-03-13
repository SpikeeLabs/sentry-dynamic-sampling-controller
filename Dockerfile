# base image
FROM python:3.10.8-alpine as python-base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VENV_PATH="/app/venv" \
    APP_PATH="/app"
# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"
WORKDIR $APP_PATH


# Build
FROM python-base as builder-base

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# get poetry
RUN apk update \
    && apk add --update --no-cache curl==7.88.1-r0 gcc=12.2.1_git20220924-r4 linux-headers=5.19.5-r0 build-base=0.5-r3 \
    && curl -sSL https://install.python-poetry.org | python -

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
FROM nginx:mainline-alpine as static
COPY --from=static-base /app/assets /usr/share/nginx/html

# Prod
FROM python-base as production
COPY --from=builder-base $APP_PATH $APP_PATH

COPY . $APP_PATH

RUN chmod u+rwx "$APP_PATH/manage.py"

CMD ["gunicorn", "controller.wsgi", "-c", "/app/config.py"]
