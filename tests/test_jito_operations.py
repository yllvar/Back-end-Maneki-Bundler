import pytest
from unittest.mock import patch, MagicMock
from src.jito_operations import create_jito_bundle
from src.token_operations import PumpPortalTrader

class TestJitoOperations:

    @pytest.fixture
    def mock_trader(self):
        trader = PumpPortalTrader()
        trader.signer_keypair = MagicMock()
        trader.mint_keypair = MagicMock()
        trader.create_ipfs_metadata = MagicMock(return_value='mock_metadata_uri')
        trader.get_token_price = MagicMock(return_value=0.000001)  # 1 SOL = 1,000,000 tokens
        return trader

    @patch('requests.post')
    def test_create_jito_bundle(self, mock_post, mock_trader):
        mock_response_transactions = MagicMock()
        mock_response_transactions.status_code = 200
        mock_response_transactions.json.return_value = ["mock_transaction_data1", "mock_transaction_data2"]

        mock_post.side_effect = [MagicMock(), mock_response_transactions, MagicMock()]

        create_jito_bundle()

        # Check if the API calls were made with the expected parameters
        mock_post.assert_any_call(
            'https://pump.fun/api/ipfs',
            data=MagicMock(),
            files=MagicMock()
        )
        mock_post.assert_any_call(
            'https://pumpportal.fun/api/trade-local',
            headers={"Content-Type": "application/json"},
            json=MagicMock()
        )

        print.assert_called_with("Jito bundle successfully executed.")

    @patch('requests.post')
    def test_create_jito_bundle_failure(self, mock_post, mock_trader):
        mock_response_transactions = MagicMock()
        mock_response_transactions.status_code = 500
        mock_response_transactions.json.return_value = {"error": "Mock error"}
        mock_post.side_effect = [MagicMock(), mock_response_transactions, MagicMock()]

        create_jito_bundle()

        print.assert_called_with("Failed to execute Jito bundle.")
        print.assert_called_with("Mock error")  # Assuming the error message is printed out