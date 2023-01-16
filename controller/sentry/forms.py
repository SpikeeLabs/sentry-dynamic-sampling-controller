from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import DurationField, FloatField, Form
from durationwidget.widgets import TimeDurationWidget


class BumpForm(Form):
    new_sample_rate = FloatField(help_text="Sample rate between 0 and 1")
    duration = DurationField(
        widget=TimeDurationWidget(show_days=False, show_seconds=False),
        help_text="Duration",
    )

    def clean_new_sample_rate(self):
        data = self.cleaned_data["new_sample_rate"]
        if data < 0 or data > 1:
            raise ValidationError("new_sample_rate must be between 0 and 1")
        return data

    def clean_duration(self):
        data = self.cleaned_data["duration"]
        if data.total_seconds() < 0 or data.total_seconds() > settings.MAX_BUMP_TIME_SEC:
            raise ValidationError(f"duration must be between 0 and {settings.MAX_BUMP_TIME_SEC}")
        return data
