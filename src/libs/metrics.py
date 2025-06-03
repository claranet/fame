import atexit
from dataclasses import dataclass
from datetime import datetime

import datadog
import logging
import os
import signalfx
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
    dd_app_key = os.environ.get("DD_APP_KEY")
    dd_api_host = os.environ.get("DD_API_HOST")

    # Check for SignalFx configuration
    sfx_token = os.environ.get("SFX_TOKEN")
    sfx_realm = os.environ.get("SFX_REALM", "eu0")

    # Prioritize Datadog if both are available
    if dd_api_key:
        logger.info("Using Datadog metrics sender")
        dd_config = {"api_key": dd_api_key}
        if dd_app_key:
            dd_config["app_key"] = dd_app_key
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
        self, name: str, type: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the backend.

        :param name: Name of the metric
        :param type: Type of metric (gauge, counter, cumulative_counter)
        :param values: List of timestamp, value and dimensions tuples
        :return: None
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close any connections and perform cleanup.

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
        app_key: str = None,
        api_host: str = "https://api.datadoghq.eu",
    ):
        """
        Initialize the Datadog metrics sender with configuration.

        :param api_key: Datadog API key
        :param app_key: Datadog application key (optional)
        :param api_host: Datadog API host (optional, default: 'https://api.datadoghq.eu')
        """
        if not api_key:
            raise ValueError("Datadog API key is required")

        self.api_key = api_key
        self.app_key = app_key
        self.api_host = api_host

        logger.info(f"Initializing Datadog metrics sender with host: {self.api_host}")

        # Initialize the Datadog client
        options = {
            "api_key": self.api_key,
            "api_host": self.api_host,
        }
        if self.app_key:
            options["app_key"] = self.app_key

        datadog.initialize(**options)

    def send_metrics(
        self, name: str, type: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the Datadog.

        :param name: Name of the metric
        :param type: Type of metric (gauge, counter, cumulative_counter)
        :param values: List of timestamp, value and dimensions tuples
        :return: None
        """
        if not values:
            logger.warning("No metrics data to send")
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

        # Send metrics in batches by dimension
        for batch in metrics_by_dimensions.values():
            datadog.api.Metric.send(
                metric=name,
                points=batch["points"],
                type=self._map_metric_type(type),
                tags=[f"{k}:{v}" for k, v in batch["dimensions"].items()],
            )
        logger.info(
            f"Sent {name} metrics to Datadog",
        )

    @staticmethod
    def _map_metric_type(metric_type: str) -> str:
        """
        Map SignalFx metric types to Datadog metric types.

        :param metric_type: SignalFx metric type
        :return: Datadog metric type
        """
        mapping = {"gauge": "gauge", "counter": "count", "cumulative_counter": "count"}
        return mapping.get(metric_type, "gauge")

    def close(self) -> None:
        """
        Close the Datadog client connection.

        :return: None
        """
        # Datadog Python client doesn't require explicit closing
        logger.info("Datadog client connection closed")


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
        if not token:
            raise ValueError("SignalFx token is required")
        self.token = token
        self.realm = realm

        logger.info(f"Initializing SignalFx metrics sender with realm: {self.realm}")

        self.sfx_client = signalfx.SignalFx(
            api_endpoint=f"https://api.{self.realm}.signalfx.com",
            ingest_endpoint=f"https://ingest.{self.realm}.signalfx.com",
            stream_endpoint=f"https://stream.{self.realm}.signalfx.com",
        )
        self.ingest = self.sfx_client.ingest(self.token)
        atexit.register(self.close)

    def send_metrics(
        self, name: str, type: str, values: List[Tuple[datetime, float, Dict[str, str]]]
    ) -> None:
        """
        Send metrics to the SignalFx.

        :param name: Name of the metric
        :param type: Type of metric (gauge, counter, cumulative_counter)
        :param values: List of timestamp and value tuples
        :param dimensions: Dictionary of dimensions (tags) to associate with the metric
        :return: None
        """
        if not values:
            logger.warning("No metrics data to send")
            return

        sfx_metrics = []
        for dt, v, dim in values:
            sfx_metrics.append(
                {
                    "metric": name,
                    "value": v,
                    "timestamp": dt.timestamp() * 1000,
                    "dimensions": dim,
                }
            )

        self.ingest.send(**{f"{type}s": sfx_metrics})
        logger.info(
            f"Sent {len(name)} metrics to SignalFx",
        )

    def close(self) -> None:
        """
        Close the SignalFx client connection.

        :return: None
        """
        if hasattr(self, "ingest") and self.ingest:
            self.ingest.stop()
            logger.info("SignalFx client connection closed")
