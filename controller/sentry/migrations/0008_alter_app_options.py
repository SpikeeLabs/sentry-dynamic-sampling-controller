# Generated by Django 4.1.6 on 2023-02-03 14:36
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sentry", "0007_app_sentry_project_slug"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="app",
            options={
                "permissions": [
                    ("bump_sample_rate_app", "Can bump sample rate"),
                    ("panic_app", "Panic! Set all sample rate to 0"),
                    ("enable_disable_metrics_app", "Can Enable/Disable metrics"),
                ]
            },
        ),
    ]
