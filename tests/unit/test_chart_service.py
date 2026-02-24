import pytest
import io
import pandas as pd
from unittest.mock import patch

from app.services.chart_service import ChartService


@pytest.fixture
def chart_service():
    return ChartService()


@pytest.fixture
def valid_dataframe():
    # Dummy-Dataframe
    return pd.DataFrame(
        {"Open": [10], "High": [20], "Low": [5], "Close": [15], "Volume": [1000]},
        index=pd.date_range("2023-01-01", periods=1),
    )


class TestChartService:
    """Tests für den ChartService"""

    @pytest.mark.asyncio
    @patch.object(ChartService, "_create_plot")
    async def test_generate_chart_async_calls_create_plot(self, mock_create_plot, chart_service):
        # Arrange
        mock_buffer = io.BytesIO(b"dummy_image_data")
        mock_create_plot.return_value = mock_buffer

        # Act
        result = await chart_service.generate_chart_async(
            crypto_symbol="btc", period="1d", interval="1h"
        )

        # Assert
        mock_create_plot.assert_called_once_with("btc", "1d", "1h")
        assert result == mock_buffer

    @patch("app.services.chart_service.yf.download")
    @patch("app.services.chart_service.mpf.plot")
    def test_create_plot_success(
        self, mock_mpf_plot, mock_yf_download, chart_service, valid_dataframe
    ):
        # Arrange
        mock_yf_download.return_value = valid_dataframe

        # Act
        result = chart_service._create_plot(crypto_symbol="btc", period="1d", interval="1h")

        # Assert
        mock_yf_download.assert_called_once_with(
            "BTC-USD", period="1d", interval="1h", progress=False
        )
        mock_mpf_plot.assert_called_once()
        assert isinstance(result, io.BytesIO)

    @patch("app.services.chart_service.yf.download")
    def test_create_plot_empty_data(self, mock_yf_download, chart_service):
        # Arrange: Simuliere leere Daten von yfinance
        mock_yf_download.return_value = pd.DataFrame()

        # Act
        result = chart_service._create_plot(crypto_symbol="eth", period="1d", interval="1h")

        # Assert
        assert result is None

    @patch("app.services.chart_service.yf.download")
    def test_create_plot_wrong_data_type(self, mock_yf_download, chart_service):
        # Arrange: Simuliere einen unerwarteten Datentyp
        mock_yf_download.return_value = [{"Open": 10}]

        # Act
        result = chart_service._create_plot(crypto_symbol="sol", period="1d", interval="1h")

        # Assert
        assert result is None

    @patch("app.services.chart_service.yf.download")
    def test_create_plot_all_nan_data(self, mock_yf_download, chart_service):
        # Arrange: Simuliere Daten, die nach dropna() leer sind
        nan_dataframe = pd.DataFrame(
            {"Open": [None], "High": [None], "Low": [None], "Close": [None]},
            index=pd.date_range("2023-01-01", periods=1),
        )
        mock_yf_download.return_value = nan_dataframe

        # Act
        result = chart_service._create_plot(crypto_symbol="ada", period="1d", interval="1h")

        # Assert
        assert result is None

    @patch("app.services.chart_service.yf.download")
    @patch("app.services.chart_service.mpf.plot")
    def test_create_plot_handles_multiindex(self, mock_mpf_plot, mock_yf_download, chart_service):
        # Arrange: Simuliere MultiIndex Spalten (oft bei yfinance der Fall)
        arrays = [
            ["Close", "Close", "Volume", "Volume"],
            ["BTC-USD", "ETH-USD", "BTC-USD", "ETH-USD"],
        ]
        multi_index = pd.MultiIndex.from_arrays(arrays)
        multi_index_df = pd.DataFrame(
            [[15, 2, 1000, 500]], index=pd.date_range("2023-01-01", periods=1), columns=multi_index
        )
        mock_yf_download.return_value = multi_index_df

        # Act
        result = chart_service._create_plot(crypto_symbol="btc", period="1d", interval="1h")

        # Assert: Verifiziere, dass mpf.plot aufgerufen wurde
        mock_mpf_plot.assert_called_once()
        assert isinstance(result, io.BytesIO)

        # Verify: Prüfe, ob das Argument, das an mpf.plot übergeben wurde, abgeflachte Spalten hat
        called_df = mock_mpf_plot.call_args[0][0]
        assert "Close" in called_df.columns
        assert "Volume" in called_df.columns
        assert not isinstance(called_df.columns, pd.MultiIndex)

    @patch("app.services.chart_service.yf.download")
    def test_create_plot_catches_exceptions(self, mock_yf_download, chart_service):
        # Arrange: Erzwinge einen Fehler während des Downloads
        mock_yf_download.side_effect = Exception("Simulierter API Fehler")

        # Act
        result = chart_service._create_plot(crypto_symbol="xrp", period="1d", interval="1h")

        # Assert: Service soll Fehler abfangen und None zurückgeben
        assert result is None
