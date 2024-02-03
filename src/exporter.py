''' DD exporter for prometheus '''
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Filename: exporter.py

import time
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, Union

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.usage_metering_api import UsageMeteringApi
from datadog_api_client.v2.model.projected_cost_response import ProjectedCostResponse

from prometheus_client import (
    Gauge,
    Counter,
    Summary,
    Histogram,
    Info,
)

logger = logging.getLogger('datadog-cost-exporter')

class MetricExporter:
    '''
        Usage data is delayed by up to 72 hours from when it was incurred. 
        It is retained for 15 months.
        https://datadog-api-client.readthedocs.io/en/latest/datadog_api_client.v2.api.html#module-datadog_api_client.v2.api.usage_metering_api
    '''
    def __init__(
        self,
        polling_interval_seconds,
        dd_api_key,
        dd_app_key,
        dd_host
    ):
        self.polling_interval_seconds = polling_interval_seconds
        self.dd_api_key = dd_api_key
        self.dd_app_key = dd_app_key
        self.dd_host = dd_host
        self.default_labels = {}
        self.metrics = {}

    def define_metrics(self):
        """
        Defines the Prometheus metrics object. 
        Returns a dictionary of metrics.
        """
        self.metrics["config_sample_metric"] = Gauge(
            "sample_metric",
            "This is a sample metric for the Datadog exporter.",
            labels=tuple(self.default_labels.keys())
        )
        return self.metrics
    
    def add_metrics(self, metrics, value=None):
        """
        Adds the retrieved metrics to the pre-defined object.
        metrics: dict
            A dictionary of Prometheus metric objects.
        """
        metrics["config_sample_metric"].add_metric(
            labels=tuple(self.default_labels.values()),
            value=None
        )

    def run_metrics_loop(self):
        while True:
            try:
                self.fetch()
            except Exception as e:
                logging.error(e)
                continue
            time.sleep(self.polling_interval_seconds)

    def get_api_instance(self):
        configuration = Configuration()
        configuration.unstable_operations["get_monthly_cost_attribution"] = True
        configuration.api_key["appKeyAuth"] = self.dd_app_key
        configuration.api_key["apiKeyAuth"] = self.dd_api_key
        with ApiClient(configuration=configuration) as api_client:
            api_instance = UsageMeteringApi(api_client)
            return api_instance

    def get_projected_total_cost(self, api_instance: Any) -> Union[None, ProjectedCostResponse]:
        try:
            projectedCostResponse = api_instance.get_projected_monthly_cost()

            for projected_cost_data in projectedCostResponse.data:
                attributes = projected_cost_data.attributes

                org_name = attributes.org_name
                public_id = attributes.public_id
                region = attributes.region
                projected_total_cost = attributes.projected_total_cost
                date = parse(attributes.date).strftime("%Y-%m-%d")

                projected_total_cost_metric_name = "projected_total_cost"
                if projected_total_cost_metric_name in self.metrics:
                    projected_total_cost_metric = self.metrics[projected_total_cost_metric_name]
                else:
                    projected_total_cost_metric = Gauge(
                        projected_total_cost_metric_name,
                        "The projected total cost for the month.",
                        labels=["org_name", "public_id", "region", "date"]
                    )
                    self.metrics[projected_total_cost_metric_name] = projected_total_cost_metric

                projected_total_cost_metric.labels(org_name, public_id, region).set(attributes.projected_total_cost)

                for charge in attributes.charges:
                    charge_type = charge.charge_type
                    cost = charge.cost
                    product_name = charge.product_name

                    charge_metric_name = f"projected_charge_cost_{product_name}"

                    if charge_metric_name in self.metrics:
                        metric_object = self.metrics[charge_metric_name]
                    else:
                        metric_object = Gauge(
                            charge_metric_name,
                            f"The projected cost for {product_name} charge.",
                            labels=["org_name", "public_id", "region", "charge_type", "date"]
                        )
                        self.metrics[charge_metric_name] = metric_object

                    labels = [org_name, public_id, region, charge.charge_type]
                    metric_object.labels(*labels).set(charge.cost)
        except Exception as e:
            logging.error(f"Error querying Datadog projected cost endpoint: {e}")
            return None

    def get_historical_cost_by_org(self, api_instance: Any) -> None:
        try:
            costByOrgResponse: Dict[str, Any] = api_instance.get_historical_cost_by_org(
                view="summary",
                start_month=(datetime.now() + relativedelta(months=-2)),
            )

            for cost_data in costByOrgResponse.get("data", []):
                attributes = cost_data.get("attributes", {})
                org_name = attributes.get("org_name", "")
                public_id = attributes.get("public_id", "")
                region = attributes.get("region", "")
                date = parse(attributes.get("date", "")).strftime("%Y-%m-%d")

                for charge in attributes.get("charges", []):
                    product_name = charge.get("product_name", "")
                    charge_type = charge.get("charge_type", "")
                    charge_cost = charge.get("cost", "")

                    charge_metric_name = f"historical_charge_cost_{product_name}"

                    if charge_metric_name in self.metrics:
                        metric_object = self.metrics[charge_metric_name]
                    else:
                        metric_object = Gauge(
                            charge_metric_name,
                            f"The historical cost for {product_name} charge.",
                            labels=["org_name", "public_id", "region", "charge_type", "date"]
                        )
                        self.metrics[charge_metric_name] = metric_object
                    labels = [org_name, public_id, region, charge_type, date]
                    metric_object.labels(*labels).set(charge_cost)
        except Exception as e:
            logging.error(f"Error handling historical cost by organization: {e}")
            return None

    def get_monthly_cost_attribution(self, api_instance: Any) -> None:
        try:
            # Get monthly cost attribution
            monthlyCostAttributionResponse: Dict[str, Any] = api_instance.get_monthly_cost_attribution(
                start_month=(datetime.now() + relativedelta(days=-5)),
                end_month=(datetime.now() + relativedelta(days=-3)),
                fields="*",
            )

            for cost_data in monthlyCostAttributionResponse.get("data", []):
                attributes = cost_data.get("attributes", {})
                org_name = attributes.get("org_name", "")
                public_id = attributes.get("public_id", "")
                date = parse(attributes.get("month", "")).strftime("%Y-%m-%d")

                for field, value in attributes.get("values", {}).items():
                    tag_metric_name = f"monthly_cost_attribution_{field}"

                    if tag_metric_name in self.metrics:
                        metric_object = self.metrics[tag_metric_name]
                    else:
                        metric_object = Gauge(
                            tag_metric_name,
                            f"The monthly cost attribution for {field} tag.",
                            labels=["org_name", "public_id", "date"]
                        )
                        self.metrics[tag_metric_name] = metric_object

                    # Set the value for the metric
                    labels = [org_name, public_id, date]
                    metric_object.labels(*labels).set(value)

            for aggregate in monthlyCostAttributionResponse.get("meta", {}).get("aggregates", []):
                agg_type = aggregate.get("agg_type", "")
                field = aggregate.get("field", "")
                value = aggregate.get("value", "")

                aggregate_metric_name = f"monthly_cost_aggregate_{field}"
                
                if aggregate_metric_name in self.metrics:
                    metric_object = self.metrics[aggregate_metric_name]
                else:
                    metric_object = Gauge(
                        aggregate_metric_name,
                        f"The monthly aggregate value for {field}.",
                        labels=["agg_type"]
                    )
                    self.metrics[aggregate_metric_name] = metric_object

                # Set the value for the metric
                metric_object.labels(agg_type).set(value)

        except Exception as e:
            logging.error(f"Error handling monthly cost attribution: {e}")
            return None

    def fetch(self):
        """
        Fetch the metrics from the Datadog API and yield them.
        """
        logger.info("Collecting the metrics for a Prometheus client")
        
        api_instance = self.get_api_instance()

        self.get_projected_total_cost(api_instance)
        self.get_historical_cost_by_org(api_instance)
        self.get_monthly_cost_attribution(api_instance)

        metric_definitions = self.define_metrics()
        self.add_metrics(metric_definitions, response)

        yield from metric_definitions.values()
