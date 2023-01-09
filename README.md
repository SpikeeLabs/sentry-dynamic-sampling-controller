# Sentry Dynamic Sampling Controller

This project aims to provide dynamic sampling without relying on Sentry Dynamic Sampling.


It work by installing the library [sentry-dynamic-sampling-lib](https://github.com/SpikeeLabs/sentry-dynamic-sampling-lib) on each project that use sentry. This lib hooks into the sentry callback to change the sampling rate. to get the rate the lib calls this service.




## Install
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

# add user
python manage.py createsuperuser

# run server
# admin @ http://localhost:8000/admin/
python manage.py runserver

```
