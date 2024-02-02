''' DD exporter for prometheus '''
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Filename: exporter.py

import time
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from prometheus_client import Gauge
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.usage_metering_api import UsageMeteringApi

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
        configuration.api_key["appKeyAuth"] = self.dd_app_key
        configuration.api_key["apiKeyAuth"] = self.dd_api_key
        with ApiClient(configuration=configuration) as api_client:
            api_instance = UsageMeteringApi(api_client)
            return api_instance

    def query_dd_cost_endpoint(self, api_instance, group_by):
        return

    def fetch(self):
        api_instance = self.get_api_instance()
        response = self.query_dd_cost_endpoint(api_instance, group_by)
        return response
