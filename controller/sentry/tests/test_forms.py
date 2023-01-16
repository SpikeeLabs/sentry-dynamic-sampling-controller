import pytest
from django.conf import settings

from controller.sentry.forms import BumpForm


@pytest.mark.parametrize("sample_rate", [-1, 2, 5])
def test_bump_form_invalid_sample_rate(sample_rate):
    data = {
        "new_sample_rate": sample_rate,
        "duration_0": 0,
        "duration_1": 5,
    }
    form = BumpForm(data)
    assert not form.is_valid()
    assert form.errors["new_sample_rate"] == ["new_sample_rate must be between 0 and 1"]


@pytest.mark.parametrize("duration", [-1, 50])
def test_bump_form_invalid_duration(duration):
    data = {
        "new_sample_rate": 1,
        "duration_0": duration,
        "duration_1": 0,
    }
    form = BumpForm(data)
    assert not form.is_valid()
    assert form.errors["duration"] == [f"duration must be between 0 and {settings.MAX_BUMP_TIME_SEC}"]
