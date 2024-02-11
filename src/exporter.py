""" DD exporter for prometheus """
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Filename: exporter.py

import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, Optional, Union

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.usage_metering_api import (
    UsageMeteringApi as V1UsageMeteringApi,
)
from datadog_api_client.v1.model.monthly_usage_attribution_supported_metrics import (
    MonthlyUsageAttributionSupportedMetrics,
)
from datadog_api_client.v2.api.usage_metering_api import UsageMeteringApi
from datadog_api_client.v2.api.spans_metrics_api import SpansMetricsApi
from datadog_api_client.v1.api.metrics_api import MetricsApi as V1MetricsApi
from datadog_api_client.v2.model.projected_cost_response import ProjectedCostResponse

from prometheus_client import (
    Gauge,
    Counter,
    Summary,
    Histogram,
    Info,
)

logger = logging.getLogger("datadog-cost-exporter")


class MetricExporter:
    """
    Usage data is delayed by up to 72 hours from when it was incurred.
    NB: It is retained for 15 months.
    """

    def __init__(
        self, polling_interval_seconds, dd_api_key, dd_app_key, dd_host, dd_debug
    ):
        self.polling_interval_seconds = polling_interval_seconds
        self.dd_api_key = dd_api_key
        self.dd_app_key = dd_app_key
        self.dd_host = dd_host
        self.dd_debug = dd_debug
        self.default_labels = {}
        self.metrics = {}

    def create_api_client(self) -> ApiClient:
        configuration = Configuration()
        configuration.unstable_operations["get_monthly_cost_attribution"] = True
        configuration.api_key["appKeyAuth"] = self.dd_app_key
        configuration.api_key["apiKeyAuth"] = self.dd_api_key
        configuration.debug = self.dd_debug
        configuration.server_variables["site"] = self.dd_host
        return ApiClient(configuration=configuration)

    def get_usage_metric_api_instance(self) -> UsageMeteringApi:
        with self.create_api_client() as api_client:
            return UsageMeteringApi(api_client)

    def get_v1_usage_metric_api_instance(self) -> V1UsageMeteringApi:
        with self.create_api_client() as api_client:
            return V1UsageMeteringApi(api_client)

    def get_spans_metrics_api_instance(self) -> SpansMetricsApi:
        with self.create_api_client() as api_client:
            return SpansMetricsApi(api_client)

    def get_v1_metrics_api_instance(self) -> V1MetricsApi:
        with self.create_api_client() as api_client:
            return V1MetricsApi(api_client)

    def define_metrics(self) -> Dict[str, Gauge]:
        """
        Defines the Prometheus metrics object.
        Returns a dictionary of metrics.
        """
        if "config_sample_metric" not in self.metrics:
            self.metrics["config_sample_metric"] = Gauge(
                "sample_metric",
                "This is a sample metric for the Datadog exporter.",
            )
        return self.metrics

    def add_metrics(
        self, metrics: Dict[str, Any] = {}, value: Optional[Any] = None
    ) -> None:
        """
        Adds the retrieved metrics to the pre-defined object.
        metrics: dict
            A dictionary of Prometheus metric objects.
        """
        for metric_name, metric_object in metrics.items():
            if metric_name not in self.metrics:
                self.metrics[metric_name] = metric_object
            else:
                logging.warning(f"Metric '{metric_name}' already added.")

    def run_metrics_loop(self):
        while True:
            try:
                self.fetch()
            except Exception as e:
                logging.error(e)
                continue
            time.sleep(self.polling_interval_seconds)

    def get_projected_total_cost(
        self, api_instance: UsageMeteringApi
    ) -> Union[None, ProjectedCostResponse]:
        try:
            projectedCostResponse = api_instance.get_projected_cost()

            for projected_cost_data in projectedCostResponse.data:
                attributes = projected_cost_data.attributes

                org_name = attributes.org_name
                public_id = attributes.public_id
                region = attributes.region
                projected_total_cost = attributes.projected_total_cost
                date = attributes.date

                projected_total_cost_metric_name = "projected_total_cost"
                if projected_total_cost_metric_name in self.metrics:
                    projected_total_cost_metric = self.metrics[
                        projected_total_cost_metric_name
                    ]
                else:
                    projected_total_cost_metric = Gauge(
                        projected_total_cost_metric_name,
                        "The projected total cost for the month.",
                        ["org_name", "public_id", "region"],
                    )
                    self.metrics[
                        projected_total_cost_metric_name
                    ] = projected_total_cost_metric

                projected_total_cost_metric.labels(
                    org_name=org_name, public_id=public_id, region=region
                ).set(attributes.projected_total_cost)

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
                            ["org_name", "public_id", "region", "charge_type", "date"],
                        )
                        self.metrics[charge_metric_name] = metric_object

                    labels = {
                        "org_name": org_name,
                        "public_id": public_id,
                        "region": region,
                        "charge_type": charge.charge_type,
                        "date": date,
                    }
                    metric_object.labels(**labels).set(charge.cost)
        except Exception as e:
            logging.error(f"Error querying Datadog projected cost endpoint: {e}")
            return None

    def get_historical_cost_by_org(self, api_instance: UsageMeteringApi) -> None:
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
                date = attributes.get("date", "")

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
                            ["org_name", "public_id", "region", "charge_type", "date"],
                        )
                        self.metrics[charge_metric_name] = metric_object

                    labels = {
                        "org_name": org_name,
                        "public_id": public_id,
                        "region": region,
                        "charge_type": charge_type,
                        "date": date,
                    }

                    metric_object.labels(**labels).set(charge_cost)
        except Exception as e:
            logging.error(f"Error handling historical cost by organization: {e}")
            return None

    def get_monthly_cost_attribution(self, api_instance: V1UsageMeteringApi) -> None:
        try:
            # Get monthly cost attribution
            monthlyCostAttributionResponse: Dict[
                str, Any
            ] = api_instance.get_monthly_usage_attribution(
                start_month=(datetime.now() + relativedelta(days=-3)).isoformat(
                    timespec="seconds"
                ),
                end_month=(datetime.now() + relativedelta(days=-3)),
                fields="*",
            )

            for cost_data in monthlyCostAttributionResponse.get("data", []):
                attributes = cost_data.get("attributes", {})
                org_name = attributes.get("org_name", "")
                public_id = attributes.get("public_id", "")
                date = attributes.get("month", "")

                for field, value in attributes.get("values", {}).items():
                    tag_metric_name = f"monthly_cost_attribution_{field}"

                    if tag_metric_name in self.metrics:
                        metric_object = self.metrics[tag_metric_name]
                    else:
                        metric_object = Gauge(
                            tag_metric_name,
                            f"The monthly cost attribution for {field} tag.",
                            ["org_name", "public_id", "date"],
                        )
                        self.metrics[tag_metric_name] = metric_object
                    labels = {
                        "org_name": org_name,
                        "public_id": public_id,
                        "date": date,
                    }
                    # Set the value for the metric
                    metric_object.labels(**labels).set(value)

            for aggregate in monthlyCostAttributionResponse.get("meta", {}).get(
                "aggregates", []
            ):
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
                        ["agg_type"],
                    )
                    self.metrics[aggregate_metric_name] = metric_object

                labels = {
                    "agg_type": agg_type,
                }
                # Set the value for the metric
                metric_object.labels(**agg_type).set(value)

        except Exception as e:
            logging.error(f"Error handling monthly cost attribution: {e}")
            return None

    def _query_timeseries_points(
        self, query, fr: datetime, to: datetime, api_instance: V1MetricsApi
    ) -> None:
        """
        Query the Datadog API for timeseries points.
        See: https://docs.datadoghq.com/account_management/billing/usage_metrics/#types-of-usage
        """
        try:
            response = api_instance.query_metrics(
                _from=int(fr.timestamp()),
                to=int(to.timestamp()),
                query=query,
            )
        except Exception as e:
            logging.error(f"Error handling metrics list: {e}")
            return None

    def get_usage_this_month(self, api_instance: V1MetricsApi) -> None:
        """
        Get the amount of logs ingested this month.
        """
        current_time = datetime.now()
        first_day_of_month = datetime.today().replace(day=1)

        # ingested spans
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.apm.ingested_bytes{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

        # index spans
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.apm.ingested_spans{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

        # ingested logs
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.logs.ingested_bytes{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

        # index logs
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.logs.ingested_events{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

        # infra host
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.hosts{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

        # rum sessions
        self._query_timeseries_points(
            "sum:datadog.estimated_usage.rum.sessions{*} by {service, env}",
            first_day_of_month,
            current_time,
            api_instance,
        )

    def fetch(self):
        """
        Fetch metrics from the Datadog API.
        """
        logger.info("Collecting metrics for a Prometheus client")

        usage_metric_api_instance = self.get_usage_metric_api_instance()
        self.get_projected_total_cost(usage_metric_api_instance)
        self.get_historical_cost_by_org(usage_metric_api_instance)

        usage_metric_api_instance_v1 = self.get_v1_usage_metric_api_instance()
        self.get_monthly_cost_attribution(usage_metric_api_instance_v1)

        metrics_api_instance = self.get_v1_metrics_api_instance()
        self.get_usage_this_month(metrics_api_instance)

        metric_definitions = self.define_metrics()
        self.add_metrics(metric_definitions, {})

        # yield from metric_definitions.values()
