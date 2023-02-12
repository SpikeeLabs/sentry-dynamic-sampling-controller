"""Detector."""

from collections import OrderedDict
from copy import copy
from statistics import mean, stdev

from controller.sentry.models import Project


class SpikesDetector:
    """SpikesDetector using Z-score based algorithm.

    Attributes:
        lag (int): The lag parameter determines how much your data will be smoothed and how adaptive the
            algorithm is to changes in the long-term average of the data. The more stationary your
            data is, the more lags you should include (this should improve the robustness of the algorithm).
            If your data contains time-varying trends, you should consider how quickly you want the algorithm
            to adapt to these trends. I.e., if you put lag at 10, it takes 10 'periods' before the algorithm's
            threshold is adjusted to any systematic changes in the long-term average. So choose the lag parameter
            based on the trending behavior of your data and how adaptive you want the algorithm to be.

        threshold (int): The threshold parameter is the number of standard deviations from the moving mean
            above which the algorithm will classify a new datapoint as being a signal.
            For example, if a new datapoint is 4.0
            standard deviations above the moving mean and the threshold parameter is set as 3.5,
            the algorithm will identify the datapoint as a signal. This parameter should be set based
            on how many signals you expect.
            For example, if your data is normally distributed, a threshold (or: z-score) of 3.5
            corresponds to a signaling probability of 0.00047 (from this table),
            which implies that you expect a signal once every 2128 datapoints (1/0.00047).
            The threshold therefore directly influences how sensitive the algorithm is
            and thereby also determines how often the algorithm signals.

        influence (float): The influence parameter determines the influence of signals on
            the algorithm's detection threshold.
            If put at 0, signals have no influence on the threshold, such that future signals are detected based on
            a threshold that is calculated with a mean and standard deviation that is not influenced by past signals.
            If put at 0.5, signals have half the influence of normal data points. Another way to think about this
            is that if you put the influence at 0, you implicitly assume stationarity
            (i.e. no matter how many signals there are, you always expect the time series to return to the
            same average over the long term).
            If this is not the case, you should put the influence parameter somewhere between 0 and 1,
            depending on the extent to which signals can systematically influence the time-varying trend of the data.
            E.g., if signals lead to a structural break of the long-term average of the time series,
            the influence parameter should be put high (close to 1)
            so the threshold can react to structural breaks quickly.
    """

    def __init__(self, lag: int = 48, threshold: int = 5, influence: float = 0) -> None:
        """Init detector.

        Args:
            lag (int): The lag
            threshold (int): The threshold
            influence (float): The influence
        """
        self.lag = lag
        self.threshold = threshold
        self.influence = influence

    @classmethod
    def from_project(cls, project: Project) -> "SpikesDetector":
        """Class method to create a `SpikesDetector` from a :Class:`controller.sentry.models.Project`.

        Args:
            project (Project): The project

        Returns:
            SpikesDetector: Detector
        """
        return cls(**project.detection_param)

    def compute_sentry(self, stats: dict) -> tuple[OrderedDict, dict[str, list]]:
        """Method to compute from a sentry stats dict.

        Args:
            stats (dict): The Sentry Stats

        Returns:
            OrderedDict: Annotated signal
            dict[str, list]: Full algorithm results
        """
        series = next(
            (group["series"]["sum(quantity)"] for group in stats["groups"] if group["by"]["outcome"] == "accepted"),
            None,
        )
        if series is None:
            raise ValueError("No series with accepted outcome")

        signal, avg_filter, std_filter = self.compute(series)

        annotated_result = OrderedDict((date, signal) for date, signal in zip(stats["intervals"], signal))
        dump = {
            "signal": signal,
            "avg_filter": avg_filter,
            "std_filter": std_filter,
            "series": series,
            "intervals": stats["intervals"],
        }
        return annotated_result, dump

    def compute(self, data) -> tuple[list[int], list[float], list[float]]:
        """Method to compute signals.

        Args:
            data (list[float]): data

        Returns:
            list[int]: Signal
            list[float]: avg filter
            list[float]: std filter
        """
        signals = [0] * self.lag
        avg_filter = [0] * self.lag
        std_filter = [0] * self.lag
        filtered_data = copy(data)
        avg_filter[self.lag - 1] = mean(data[: self.lag])
        std_filter[self.lag - 1] = stdev(data[: self.lag])

        for i, item in enumerate(data[self.lag :], start=self.lag):
            if abs(item - avg_filter[i - 1]) > self.threshold * std_filter[i - 1]:
                signals.append(1 if item > avg_filter[i - 1] else 0)
                filtered_data[i] = self.influence * item + (1 - self.influence) * filtered_data[i - 1]
            else:
                signals.append(0)
                filtered_data[i] = data[i]
            avg_filter.append(mean(filtered_data[(i - self.lag) : i]))
            std_filter.append(stdev(filtered_data[(i - self.lag) : i]))

        return signals, avg_filter, std_filter
