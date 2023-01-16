# Generated by Django 4.1.5 on 2023-01-12 12:39

from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations


def apply_migration(apps, schema_editor):
    emit_post_migrate_signal(2, False, "default")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    owner = Group(name="Owner")
    admin = Group(name="Admin")
    developer = Group(name="Developer")
    viewer = Group(name="Viewer")

    Group.objects.bulk_create([owner, admin, developer, viewer])

    owner.permissions.set(Permission.objects.all())
    admin.permissions.set(Permission.objects.filter(content_type__app_label="sentry", content_type__model="app"))
    developer.permissions.set(Permission.objects.filter(codename__in=["bump_sample_rate_app", "view_app"]))
    viewer.permissions.set(Permission.objects.filter(codename__in=["view_app"]))


def revert_migration(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Admin", "Owner", "Developer", "Viewer"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "__latest__"),
        ("auth", "__latest__"),
        ("admin", "__latest__"),
        ("sessions", "__latest__"),
        ("sentry", "0005_alter_app_celery_metrics_alter_app_wsgi_metrics"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="app",
            options={
                "permissions": [
                    ("bump_sample_rate_app", "Can bump sample rate"),
                    ("panic_app", "Panic! Set all sample rate to 0"),
                ]
            },
        ),
        migrations.RunPython(apply_migration, revert_migration),
    ]