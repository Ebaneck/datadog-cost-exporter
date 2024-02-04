import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from dateutil.parser import parse

from src.exporter import MetricExporter


class TestMetricExporter(unittest.TestCase):
    def setUp(self):
        self.exporter = MetricExporter(
            polling_interval_seconds=60,
            dd_api_key="your_api_key",
            dd_app_key="your_app_key",
            dd_host="your_dd_host",
            dd_debug=False,
        )

    @patch("src.exporter.time.sleep", side_effect=InterruptedError)
    @patch("src.exporter.MetricExporter.fetch")
    def test_run_metrics_loop(self, mock_fetch, mock_sleep):
        with self.assertRaises(InterruptedError):
            self.exporter.run_metrics_loop()

        mock_fetch.assert_called_once()

    @patch("src.exporter.ApiClient")
    @patch("src.exporter.UsageMeteringApi")
    def test_get_api_instance(self, mock_usage_metering_api, mock_api_client):
        api_instance = self.exporter.get_api_instance()

        mock_api_client.assert_called_once()
        mock_api_client.return_value.__enter__.assert_called_once()
        mock_usage_metering_api.assert_called_once_with(
            mock_api_client.return_value.__enter__.return_value
        )

        self.assertEqual(
            mock_api_client.call_args[1]["configuration"].api_key["appKeyAuth"],
            "your_app_key",
        )
        self.assertEqual(
            mock_api_client.call_args[1]["configuration"].api_key["apiKeyAuth"],
            "your_api_key",
        )

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

        self.exporter.get_projected_total_cost(mock_api_instance)

    # Add more test cases as needed


if __name__ == "__main__":
    unittest.main()
