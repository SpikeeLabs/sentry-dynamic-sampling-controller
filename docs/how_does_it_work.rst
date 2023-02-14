How does it work
================


This project aims to provide dynamic sampling without relying on Sentry Dynamic Sampling.


It work by installing the library `sentry-dynamic-sampling-lib <https://github.com/SpikeeLabs/sentry-dynamic-sampling-lib>`_
on each project that use sentry. This lib hooks into the sentry callback to change the sampling rate.
To get the rate the lib calls this service.


Regularly the lib update his sample rate from the controller.


On the controller you can configure the sample rate for each :class:`app <controller.sentry.models.App>` (Where an app is defined by it's sentry id, ENV, and command name).

App Key
-------
If you have 2 app deployed in to environment (staging, pre-prod) you will have 2 apps in sentry controller

 * sentryid_staging_python
 * sentryid_preprod_python

If you have multiple processes (worker and api) you will have 2 apps in sentry controller

 * sentryid_staging_celery
 * sentryid_staging_wsgi


Project
-------
Project regroup apps by theirs sentry_id. Project are created automatically after apps creation.
Project are use to get information's from Sentry API.


Bump Sample Rate
----------------
Developer can bump the sample rate for any app, but they must provide an active duration. At the end of the window the sample rate is set back to it's default value.
This allow user to set and forget without exploding your sentry quotas.


Panic Mode
----------
If you still reach your sentry quotas, you can enable the panic mode. This mode set all sample rate to 0 without changing it in the database.


Smart Features
--------------
Every hour the controller fetch every project stats on Sentry. Using this stats we can detect misbehaving apps.
For each misbehaving we create one :class:`event <controller.sentry.models.Event>` when the surge in transaction starts and one when it's end.

For now, the controller does not act on misbehaving apps.
