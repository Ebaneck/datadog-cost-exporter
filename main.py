#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Filename: main.py

import os
import sys
import logging
from config.config import get_configs
from src.exporter import MetricExporter
from prometheus_client import start_http_server

def main(config):
    app_metrics = MetricExporter(
        polling_interval_seconds=config["polling_interval_seconds"],
        dd_api_key=config["dd_api_key"],
        dd_app_key=config["dd_app_key"],
        dd_host=config["dd_host"]
    )
    start_http_server(config["exporter_port"])
    app_metrics.run_metrics_loop()


if __name__ == "__main__":
    logger_format = "%(asctime)-15s %(levelname)-8s %(message)s"
    logging.basicConfig(level=logging.INFO, format=logger_format)
    config = get_configs()
    main(config)