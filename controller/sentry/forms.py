from django.forms import DurationField, FloatField, Form

# WIDGET


class BumpForm(Form):
    new_sample_rate = FloatField(help_text="Sample rate between 0 and 1")
    duration = DurationField(help_text="Duration in second")
