"""Forms."""
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import DurationField, FloatField, Form, MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from durationwidget.widgets import TimeDurationWidget

from controller.sentry.choices import MetricType

if TYPE_CHECKING:  # pragma: no cover
    from datetime import timedelta


class BumpForm(Form):
    """BumpForm is used to bump sample rate for a set amount of time."""

    new_sample_rate = FloatField(help_text="Sample rate between 0 and 1", initial=0.5)
    duration = DurationField(
        widget=TimeDurationWidget(show_days=False, show_seconds=False), help_text="Duration", initial="0:30:00"
    )

    def clean_new_sample_rate(self) -> float:
        """This method clean the new_sample_rate.

        Returns:
            float: The cleaned sample rate

        Raises:
            ValidationError: if the sample rate is not between 0 and 1

        """
        data = self.cleaned_data["new_sample_rate"]
        if data < 0 or data > 1:
            raise ValidationError("new_sample_rate must be between 0 and 1")
        return data

    def clean_duration(self) -> "timedelta":
        """This method clean the duration.

        Returns:
            timedelta: The cleaned duration

        Raises:
            ValidationError: if the duration is not between 0 and settings.MAX_BUMP_TIME_SEC

        """
        data = self.cleaned_data["duration"]
        if data.total_seconds() < 0 or data.total_seconds() > settings.MAX_BUMP_TIME_SEC:
            raise ValidationError(f"duration must be between 0 and {settings.MAX_BUMP_TIME_SEC}")
        return data


class MetricForm(Form):
    """MetricForm is used to push new metric to the controller."""

    metrics = MultipleChoiceField(
        choices=MetricType.choices,
        widget=CheckboxSelectMultiple,
        required=False,
        help_text="Disable or Enable metric gathering",
    )
