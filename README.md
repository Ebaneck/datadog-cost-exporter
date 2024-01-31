# datadog-cost-exporter
Exposing Datadog cost information as standard Prometheus metrics

This tool is developed to streamline the aggregation of organizational cost-related metrics for users seeking to centralize and monitor their cost information.

By leveraging Datadog APIs, this exporter fetches cost information and converts it into standard Prometheus metrics.

Future updates will introduce Grafana dashboards to enhance visualization and facilitate in-depth analysis of the exported data.


### Building with Docker

```
docker build -t datadog-cost-exporter .
```

### Running with Docker

```
docker run --rm -v $(pwd):/config \
    -p 9091:9091 \
    --name datadog-cost-exporter \
    -e DD_API_KEY=${DD_API_KEY} \
    -e DD_APP_KEY=${DD_APP_KEY} \
    claudeforlife/datadog-cost-exporter:latest --config.file=/config/dd_cost_exporter_config.yaml
```

### Sample output

Todo:

### Prometheus configuration

```
- job_name: 'datadog-cost-exporter'
  metrics_path: '/metrics'
  scrape_timeout: 60s
  scrape_interval: 1800s
  static_configs:
  - targets: ['localhost:9091']
```

#### Credits

The `Datadog-cost-exporter` is inspired by [Azure-cost-exporter](https://github.com/opensourceelectrolux/azure-cost-exporter) && [Aws-cost-exporter](https://github.com/opensourceelectrolux/aws-cost-exporter/tree/main)
