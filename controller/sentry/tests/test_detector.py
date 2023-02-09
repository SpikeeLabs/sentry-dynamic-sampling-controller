import json

import pytest

from controller.sentry.detector import SpikesDetector
from controller.sentry.models import Project


@pytest.fixture(
    name="all_json",
    params=[
        ("controller/sentry/tests/data/example-1/stats.json", "controller/sentry/tests/data/example-1/expected.json"),
    ],
)
def _all_json(request):
    with open(request.param[0]) as stats_file, open(request.param[1]) as expected_file:
        stats = json.load(stats_file)
        expected = json.load(expected_file)
    return stats, expected


@pytest.mark.django_db
def test_spike_detector(all_json: tuple[dict]):
    stats, expected = all_json
    project = Project(sentry_id=123)
    detector = SpikesDetector.from_project(project)
    assert detector.lag == project.detection_param["lag"]
    assert detector.threshold == project.detection_param["threshold"]
    assert detector.influence == project.detection_param["influence"]

    res = detector.compute_sentry(stats)

    assert res == expected


@pytest.mark.django_db
def test_spike_detector_empty():
    project = Project(sentry_id=123)
    detector = SpikesDetector.from_project(project)
    assert detector.lag == project.detection_param["lag"]
    assert detector.threshold == project.detection_param["threshold"]
    assert detector.influence == project.detection_param["influence"]

    with pytest.raises(ValueError):
        detector.compute_sentry({"groups": []})
