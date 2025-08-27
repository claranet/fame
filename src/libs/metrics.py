from dataclasses import dataclass
from datetime import datetime

import datadog
import json
import logging
import os
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

logger = logging.getLogger("metrics")


def get_metrics_sender() -> "MetricsSender":
    """
    Factory function to create and return the appropriate metrics sender based on environment variables.

    Prioritizes Datadog if both Datadog and SignalFx configurations are available.

    :return: An instance of a MetricsSender implementation
    """
    # Check for Datadog configuration
    dd_api_key = os.environ.get("DD_API_KEY")
    dd_api_host = os.environ.get("DD_API_HOST")

    # Check for SignalFx configuration
    sfx_token = os.environ.get("SFX_TOKEN")
    sfx_realm = os.environ.get("SFX_REALM")

    # Prioritize Datadog if both are available
    if dd_api_key:
        logger.info("Using Datadog metrics sender")
        dd_config = {"api_key": dd_api_key}
        if dd_api_host:
            dd_config["api_host"] = dd_api_host
        return DatadogMetricsSender(**dd_config)
    elif sfx_token:
        logger.info("Using SignalFx metrics sender")
        sfx_config = {
            "token": sfx_token,
        }
        if sfx_realm:
            sfx_config["realm"] = sfx_realm
        return SignalFxMetricsSender(**sfx_config)
    else:
        raise ValueError(
            "No metrics backend configuration found. "
            "Please provide either Datadog (DD_API_KEY) or SignalFx (SFX_TOKEN) credentials.",
        )


@dataclass
class MetricsSender(ABC):
    """
    Abstract base class defining the interface for sending metrics to different backends.
    """

    @abstractmethod
    def __init__(self):
        """
        Initialize the metrics sender with configuration.
        """
        pass

    @abstractmethod
    def send_metrics(
        self, name: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the backend.

        :param name: Name of the metric
        :param values: List of timestamp, value and dimensions tuples
        :return: None
        """
        pass


class DatadogMetricsSender(MetricsSender):
    """
    Implementation of MetricsSender for Datadog.
    """

    def __init__(
        self,
        api_key: str,
        api_host: str = "https://api.datadoghq.eu",
    ):
        """
        Initialize the Datadog metrics sender with configuration.

        :param api_key: Datadog API key
        :param api_host: Datadog API host (optional, default: 'https://api.datadoghq.eu')
        """
        if not api_key:
            raise ValueError("Datadog API key is required")

        self.api_key = api_key
        self.api_host = api_host

        logger.debug(f"Initializing Datadog metrics sender with host: {self.api_host}")

        # Initialize the Datadog client
        datadog.initialize(api_key=self.api_key, api_host=self.api_host)

    def send_metrics(
        self, name: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the Datadog.

        :param name: Name of the metric
        :param values: List of timestamp, value and dimensions tuples
        :return: None
        """
        if not values:
            logger.warning(f"No metrics data to send for {name}")
            return

        # Group metrics by dimensions to minimize API calls
        metrics_by_dimensions = {}
        for dt, value, dimensions in values:
            dim_key = frozenset(dimensions.items())  # Make dimensions hashable
            if dim_key not in metrics_by_dimensions:
                metrics_by_dimensions[dim_key] = {
                    "points": [],
                    "dimensions": dimensions,
                }
            metrics_by_dimensions[dim_key]["points"].append((dt.timestamp(), value))

        # Send metrics to Datadog
        for batch in metrics_by_dimensions.values():
            logger.debug(
                f"Sending metric {name} with points {batch['points']} and dimensions {batch['dimensions']}"
            )
            datadog.api.Metric.send(
                metric=name,
                points=batch["points"],
                type="gauge",
                tags=[f"{k}:{v}" for k, v in batch["dimensions"].items()],
            )
        logger.info(f"Sent {name} metrics to Datadog")


class SignalFxMetricsSender(MetricsSender):
    """
    Implementation of MetricsSender for SignalFx/Splunk Observability.
    """

    def __init__(self, token: str, realm: str = "eu0"):
        """
        Initialize the SignalFx metrics sender with configuration.

        :param token: SignalFx access token
        :param realm: SignalFx realm (default: 'eu0')
        """
        logger.info(f"Initializing SignalFx metrics sender with realm: {realm}")
        if not token:
            raise ValueError("SignalFx token is required")

        self.url = f"https://ingest.{realm}.signalfx.com/v2/datapoint"
        self.http_headers = {
            "Content-Type": "application/json",
            "X-SF-TOKEN": token,
        }

    def send_metrics(
        self, name: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the SignalFx.

        :param name: Name of the metric
        :param values: List of timestamp and value tuples
        :return: None
        """
        if not values:
            logger.warning(f"No metrics data to send for {name}")
            return

        sfx_metrics = []
        for dt, v, dim in values:
            logger.debug(
                f"Sending metric {name} with value {v} at {dt} and dimensions {dim}"
            )
            sfx_metrics.append(
                {
                    "metric": name,
                    "value": v,
                    "timestamp": dt.timestamp() * 1000,
                    "dimensions": dim,
                }
            )

        res = requests.post(
            self.url, headers=self.http_headers, data=json.dumps({"gauge": sfx_metrics})
        )
        res.raise_for_status()

        logger.info(f"Sent {name} metrics to SignalFx")
