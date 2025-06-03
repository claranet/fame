# Metrics System Documentation

## Overview

The metrics system provides a flexible way to send metrics to different monitoring backends. Currently, it supports two backends:

1. **Datadog** - A popular cloud monitoring service
2. **SignalFx** (Splunk Observability) - Another powerful monitoring platform

The system uses a factory pattern to create the appropriate metrics sender based on configuration. The architecture consists of:

- An abstract base class `MetricsSender` that defines the interface for all metrics senders
- Two concrete implementations: `SignalFxMetricsSender` and `DatadogMetricsSender`
- A factory function `get_metrics_sender()` that determines which implementation to use based on configuration

The system is designed to be easily extensible, allowing for additional backends to be added in the future.

## Architecture

```
                                 ┌─────────────────┐
                                 │                 │
                                 │ get_metrics_sender │
                                 │    (factory)    │
                                 │                 │
                                 └────────┬────────┘
                                          │
                                          │ creates
                                          ▼
                      ┌───────────────────────────────────┐
                      │                                   │
                      │         MetricsSender             │
                      │         (abstract)                │
                      │                                   │
                      └───────────────────────────────────┘
                                 ▲           ▲
                                 │           │
                    implements   │           │  implements
                                 │           │
          ┌─────────────────────┘           └──────────────────────┐
          │                                                        │
┌─────────┴───────────────┐                           ┌────────────┴────────────┐
│                         │                           │                         │
│  SignalFxMetricsSender  │                           │  DatadogMetricsSender   │
│                         │                           │                         │
└─────────────────────────┘                           └─────────────────────────┘
          │                                                        │
          │ sends to                                    sends to   │
          ▼                                                        ▼
┌─────────────────────────┐                           ┌─────────────────────────┐
│                         │                           │                         │
│        SignalFx         │                           │        Datadog          │
│                         │                           │                         │
└─────────────────────────┘                           └─────────────────────────┘
```

## Configuration

### Environment Variables

The metrics system can be configured using environment variables:

#### Datadog Configuration

| Environment Variable | Description | Required | Default |
|---------------------|-------------|----------|---------|
| `DD_API_KEY` | Datadog API key | Yes | - |
| `DD_APP_KEY` | Datadog application key | No | - |
| `DD_API_HOST` | Datadog API host | No | `https://api.datadoghq.com` |

#### SignalFx Configuration

| Environment Variable | Description | Required | Default |
|---------------------|-------------|----------|---------|
| `SFX_TOKEN` | SignalFx access token | Yes | - |
| `SFX_REALM` | SignalFx realm | No | `eu0` |
| `SFX_EXTRA_DIMENSIONS` | Additional dimensions to add to all metrics (format: `key1=value1,key2=value2`) | No | - |

### Direct Configuration

You can also provide configuration directly when calling `get_metrics_sender()`:

```python
from libs.metrics import get_metrics_sender

# Datadog configuration
dd_config = {
    "dd_api_key": "your-datadog-api-key",
    "dd_app_key": "your-datadog-app-key",  # Optional
    "dd_api_host": "https://api.datadoghq.eu"  # Optional
}

# SignalFx configuration
sfx_config = {
    "sfx_token": "your-signalfx-token",
    "sfx_realm": "us1",  # Optional, default is "eu0"
    "sfx_extra_dimensions": "env=prod,service=my-service"  # Optional
}

# Create a metrics sender with Datadog configuration
metrics_sender = get_metrics_sender(dd_config)

# Or with SignalFx configuration
metrics_sender = get_metrics_sender(sfx_config)
```

### Backend Selection

If both Datadog and SignalFx configurations are provided, the system will prioritize Datadog. This behavior is consistent whether using environment variables or direct configuration.

## Usage

### Basic Usage

```python
from libs.metrics import get_metrics_sender

# Get a metrics sender instance (configuration from environment variables)
metrics_sender = get_metrics_sender()

# Create metrics data
metrics_data = [
   {
      "metric": "my.metric.name",
      "value": 42,
      "timestamp": 1622547600000,  # Milliseconds since epoch
      "dimensions": {"host": "my-host", "service": "my-service"}
   }
]

# Send metrics as a gauge
metrics_sender.send_metrics(metrics_data, "", "", "")

# Don't forget to close the connection when done
metrics_sender.close()
```

### Metric Types

The system supports the following metric types:

| Metric Type | Description |
|-------------|-------------|
| `gauge` | A point-in-time measurement (e.g., temperature, memory usage) |
| `counter` | A count of occurrences (e.g., API requests, errors) |
| `cumulative_counter` | A counter that accumulates over time (e.g., total bytes sent) |

### Metrics Data Format

The `metrics_data` parameter for `send_metrics()` should be a list of dictionaries with the following structure:

```python
{
    "metric": "metric.name",  # The name of the metric
    "value": 42,  # The value of the metric
    "timestamp": 1622547600000,  # Timestamp in milliseconds since epoch
    "dimensions": {  # Additional dimensions/tags for the metric
        "host": "my-host",
        "service": "my-service",
        # ... other dimensions
    }
}
```

## Integration with Azure Functions

The metrics system is designed to work seamlessly with Azure Functions. Here's an example of how to use it in an Azure Function:

```python
import os
import logging
from libs.metrics import get_metrics_sender


def main(context):
   # Initialize the metrics sender
   try:
      metrics_sender = get_metrics_sender()
   except ValueError as e:
      logging.error(f"Failed to initialize metrics sender: {e}")
      return

   # Create metrics data
   metrics_data = [
      {
         "metric": "azure.function.invocation",
         "value": 1,
         "timestamp": int(context.timestamp.timestamp() * 1000),
         "dimensions": {
            "function_name": context.function_name,
            "invocation_id": context.invocation_id
         }
      }
   ]

   # Send metrics
   metrics_sender.send_metrics(metrics_data, "", "", "")

   # Close the metrics sender
   metrics_sender.close()
```

## Migration Guide

### From SignalFx-only to Multi-backend

If you were using the previous SignalFx-only implementation, here's how to migrate to the new multi-backend system:

1. **No Code Changes Required**: The interface remains the same, so existing code using the metrics system should work without changes.

2. **Configuration Changes**:
   - Previous: `SFX_TOKEN`, `SFX_REALM`, `SFX_EXTRA_DIMENSIONS`
   - New: Same environment variables are supported

3. **Adding Datadog Support**:
   - To use Datadog instead of SignalFx, set the Datadog environment variables (`DD_API_KEY`, etc.)
   - If both Datadog and SignalFx configurations are provided, Datadog will be used

4. **Testing**:
   - Run your existing tests to ensure they still work with the new implementation
   - Add new tests for Datadog if you plan to use it

### Example Migration

Before:

```python
import os
from libs.metrics import get_metrics_sender

# SignalFx configuration
os.environ["SFX_TOKEN"] = "your-signalfx-token"
os.environ["SFX_REALM"] = "us1"
os.environ["SFX_EXTRA_DIMENSIONS"] = "env=prod,service=my-service"

# Get metrics sender (SignalFx only)
metrics_sender = get_metrics_sender()

# Send metrics
metrics_sender.send_metrics(metrics_data, "", "", "")

# Close connection
metrics_sender.close()
```

After (using Datadog):

```python
import os
from libs.metrics import get_metrics_sender

# Datadog configuration
os.environ["DD_API_KEY"] = "your-datadog-api-key"
os.environ["DD_APP_KEY"] = "your-datadog-app-key"  # Optional
os.environ["DD_API_HOST"] = "https://api.datadoghq.eu"  # Optional

# Get metrics sender (now uses Datadog)
metrics_sender = get_metrics_sender()

# Send metrics (same interface)
metrics_sender.send_metrics(metrics_data, "", "", "")

# Close connection (same interface)
metrics_sender.close()
```

## Best Practices

1. **Always close the connection**: Use `metrics_sender.close()` when you're done sending metrics to properly clean up resources.

2. **Error handling**: Wrap metrics operations in try/except blocks to prevent metrics issues from affecting your main application logic.

3. **Batch metrics**: When possible, batch multiple metrics into a single `send_metrics()` call rather than making multiple calls.

4. **Use meaningful dimensions**: Add relevant dimensions to your metrics to make them more useful for filtering and analysis.

5. **Choose the right metric type**: Use the appropriate metric type (gauge, counter, cumulative_counter) for your data.

6. **Consistent naming**: Use a consistent naming scheme for your metrics to make them easier to find and understand.

## Extending the System

To add support for a new metrics backend:

1. Create a new class that implements the `MetricsSender` interface
2. Update the factory function to create instances of your new class based on configuration
3. Add appropriate tests for your new implementation

Example:

```python
from .metrics_sender import MetricsSender

class NewBackendMetricsSender(MetricsSender):
    def __init__(self, config):
        # Initialize your backend
        pass

    def send_metrics(self, metrics_data, metric_type):
        # Send metrics to your backend
        pass

    def close(self):
        # Close connection to your backend
        pass
```

Then update the factory:

```python
def get_metrics_sender(config=None):
    # Existing code...

    # Check for new backend configuration
    new_backend_api_key = config.get("new_backend_api_key") or os.environ.get("NEW_BACKEND_API_KEY")

    # Add new backend to the priority list
    if new_backend_api_key:
        logger.info("Using New Backend metrics sender")
        new_backend_config = {
            "api_key": new_backend_api_key,
            # Other configuration...
        }
        return NewBackendMetricsSender(new_backend_config)
    elif dd_api_key:
        # Existing Datadog code...
    elif sfx_token:
        # Existing SignalFx code...
    else:
        # Error handling...
