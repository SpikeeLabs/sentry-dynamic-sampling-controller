from django.core import serializers


class ImportFixture:
    def __init__(self, *files) -> None:
        self.files = files
        self.format = format

    def __call__(self):
        return self.load_fixture, self.unload_fixture

    def get_objects(self):
        for file in self.files:
            with open(file) as fixture:
                objects = serializers.deserialize(
                    "json", fixture, ignorenonexistent=True
                )
                for obj in objects:
                    yield obj

    def load_fixture(self, apps, schema_editor):
        for obj in self.get_objects():
            obj.save()

    def unload_fixture(self, apps, schema_editor):
        for obj in self.get_objects():
            model = apps.get_model(obj.object._meta.label)
            kwargs = dict()
            if "id" in obj.object.__dict__:
                kwargs.update(id=obj.object.__dict__.get("id"))
            elif "slug" in obj.object.__dict__:
                kwargs.update(slug=obj.object.__dict__.get("slug"))
            else:
                kwargs.update(**obj.object.__dict__)
            try:
                model.objects.get(**kwargs).delete()
            except model.DoesNotExist:
                pass
