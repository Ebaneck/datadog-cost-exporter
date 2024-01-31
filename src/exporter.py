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


class MetricExporter:
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

    def get_dd_account_session(self):
        configuration = Configuration()
        return

    def query_dd_cost_endpoint(self, dd_client, group_by):
        return

    def fetch(self):
        dd_client = self.get_dd_account_session()
        response = self.query_dd_cost_endpoint(dd_client, group_by)
        return response
