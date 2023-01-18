# Sentry Dynamic Sampling Controller

![Tests Status](https://github.com/SpikeeLabs/sentry-dynamic-sampling-controller/actions/workflows/.github/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/SpikeeLabs/sentry-dynamic-sampling-controller/branch/main/graph/badge.svg?token=JS0XEL56JT)](https://codecov.io/gh/SpikeeLabs/sentry-dynamic-sampling-controller)
---

This project aims to provide dynamic sampling without relying on Sentry Dynamic Sampling.


It work by installing the library [sentry-dynamic-sampling-lib](https://github.com/SpikeeLabs/sentry-dynamic-sampling-lib) on each project that use sentry. This lib hooks into the sentry callback to change the sampling rate. To get the rate the lib calls this service.




## Development
```bash
# install deps
poetry install

# pre-commit
poetry run pre-commit install --install-hook
poetry run pre-commit install --install-hooks --hook-type commit-msg
```


## Run
```bash
poetry shell

python manage.py migrate

# add user
python manage.py createsuperuser

# run server
# admin @ http://localhost:8000/admin/
python manage.py runserver

```
