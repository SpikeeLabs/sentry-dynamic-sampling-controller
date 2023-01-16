# Generated by Django 4.1.5 on 2023-01-11 08:08

import django_better_admin_arrayfield.models.fields
from django.db import migrations, models

import controller.sentry.models


class Migration(migrations.Migration):

    dependencies = [
        ("sentry", "0002_app_wsgi_ignore_path_alter_app_reference"),
    ]

    operations = [
        migrations.AddField(
            model_name="app",
            name="celery_ignore_task",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=50),
                blank=True,
                default=controller.sentry.models.get_default_celery_ignore_task,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="app",
            name="celery_metrics",
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name="app",
            name="wsgi_metrics",
            field=models.JSONField(null=True),
        ),
    ]