# datadog-cost-exporter
[![Docker Build & Release](https://github.com/Ebaneck/datadog-cost-exporter/actions/workflows/release.yml/badge.svg)](https://github.com/Ebaneck/datadog-cost-exporter/actions/workflows/release.yml) ![GitHub Tag](https://img.shields.io/github/v/tag/Ebaneck/datadog-cost-exporter) [![Pre-merge checks](https://github.com/Ebaneck/datadog-cost-exporter/actions/workflows/pr.yml/badge.svg)](https://github.com/Ebaneck/datadog-cost-exporter/actions/workflows/pr.yml) [![Coverage Status](https://coveralls.io/repos/github/Ebaneck/datadog-cost-exporter/badge.svg?branch=main)](https://coveralls.io/github/Ebaneck/datadog-cost-exporter?branch=main)


This tool is developed to streamline the aggregation of organizational cost-related metrics for users seeking to centralize and monitor their cost information. By leveraging Datadog APIs, this exporter fetches cost information and converts it into standard Prometheus metrics.

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

```
# HELP projected_total_cost The projected total cost for the month.
# TYPE projected_total_cost gauge
projected_total_cost{org_name="my-org",public_id="random-uuid",region="eu"} 0.0
# HELP historical_charge_cost_apm_host The historical cost for apm_host charge.
# TYPE historical_charge_cost_apm_host gauge
historical_charge_cost_apm_host{charge_type="committed",date="2023-12-01 00:00:00+00:00",org_name="my-org",public_id="random-uuid",region="eu"} 5108.07
# HELP historical_charge_cost_ingested_spans The historical cost for ingested_spans charge.
# TYPE historical_charge_cost_ingested_spans gauge
historical_charge_cost_ingested_spans{charge_type="on_demand",date="2023-12-01 00:00:00+00:00",org_name="my-org",public_id="random-uuid",region="eu"} 1916.5
```

### Prometheus configuration

```
- job_name: 'datadog-cost-exporter'
  metrics_path: '/metrics'
  scrape_timeout: 60s
  static_configs:
  - targets: ['localhost:9091']
```

### Contributing

Contributions are what makes the open-source community an amazing place to learn, inspire, and create. 

Please try to create bug reports that:

- Include steps to reproduce the problem.
- Include as much detail as possible.
- Do not duplicate existing opened issues.

#### Credits

The `Datadog-cost-exporter` is inspired by [Azure-cost-exporter](https://github.com/opensourceelectrolux/azure-cost-exporter) && [Aws-cost-exporter](https://github.com/opensourceelectrolux/aws-cost-exporter/tree/main)
