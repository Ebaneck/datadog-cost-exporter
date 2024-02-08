import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime
from dateutil.parser import parse

from src.exporter import MetricExporter


class TestMetricExporter(unittest.TestCase):
    def setUp(self):
        self.dd_api_key = "your_dd_api_key"
        self.dd_app_key = "your_dd_app_key"
        self.dd_host = "your_dd_host"
        self.dd_debug = True
        self.polling_interval_seconds = 60
        self.metric_exporter = MetricExporter(
            self.polling_interval_seconds,
            self.dd_api_key,
            self.dd_app_key,
            self.dd_host,
            self.dd_debug,
        )

    def test_create_api_client(self):
        api_client = self.metric_exporter.create_api_client()
        self.assertIsNotNone(api_client)

    # @patch('src.exporter.UsageMeteringApi')
    # def test_get_usage_metric_api_instance(self, mock_api):
    #     api_instance = self.metric_exporter.get_usage_metric_api_instance()
    #     mock_api.assert_called_once_with(api_instance.api_client)

    # @patch('src.exporter.SpansMetricsApi')
    # def test_get_spans_metrics_api_instance(self, mock_api):
    #     api_instance = self.metric_exporter.get_spans_metrics_api_instance()
    #     mock_api.assert_called_once_with(api_instance.api_client)

    def test_define_metrics(self):
        metrics = self.metric_exporter.define_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("config_sample_metric", metrics)
        self.assertTrue(metrics["config_sample_metric"]._name == "sample_metric")

    def test_add_metrics(self):
        mock_metric = MagicMock()
        metrics = {"mock_metric": mock_metric}
        self.metric_exporter.add_metrics(metrics)
        self.assertIn("mock_metric", self.metric_exporter.metrics)
        self.assertEqual(self.metric_exporter.metrics["mock_metric"], mock_metric)

    @patch("src.exporter.time.sleep", side_effect=InterruptedError)
    @patch("src.exporter.MetricExporter.fetch")
    def test_run_metrics_loop(self, mock_fetch, mock_sleep):
        with self.assertRaises(InterruptedError):
            self.metric_exporter.run_metrics_loop()

        mock_fetch.assert_called_once()

    @patch("src.exporter.UsageMeteringApi")
    def test_get_projected_total_cost(self, mock_usage_metering_api):
        mock_api_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(
                attributes=MagicMock(
                    org_name="TestOrg",
                    public_id="TestPublicId",
                    region="TestRegion",
                    projected_total_cost=100.0,
                    date=datetime.now(),
                    charges=[
                        MagicMock(
                            charge_type="TestChargeType",
                            cost=50.0,
                            product_name="TestProduct",
                        )
                    ],
                )
            )
        ]
        mock_api_instance.get_projected_monthly_cost.return_value = mock_response

        self.metric_exporter.get_projected_total_cost(mock_api_instance)

    # Add more test cases as needed


if __name__ == "__main__":
    unittest.main()
