# Generated by Django 4.1.5 on 2023-01-12 12:39

from django.db import migrations

from controller.sentry.migrations import ImportFixture


class Migration(migrations.Migration):

    dependencies = [
        ("sentry", "0005_alter_app_celery_metrics_alter_app_wsgi_metrics"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="app",
            options={"permissions": [("bump_sample_rate_app", "Can bump sample rate")]},
        ),
        migrations.RunPython(
            *ImportFixture("controller/sentry/fixtures/groups.json")()
        ),
    ]
