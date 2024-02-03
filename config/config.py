import os
import sys
import argparse
import logging
from envyaml import EnvYAML


def get_configs():
    parser = argparse.ArgumentParser(
        description="Datadog Cost Exporter, exposing Datadog cost data as Prometheus metrics."
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="The config file (dd_cost_exporter_config.yaml) for the exporter",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        logging.error("DD Cost Exporter config file does not exist!")
        sys.exit(1)

    config = EnvYAML(args.config)

    # config validation
    required_keys = ["dd_api_key", "dd_app_key"]
    for key in required_keys:
        if len(config[key]) == 0:
            logging.error(f"There should be at least {key} defined in the config!")
            sys.exit(1)

    return config
