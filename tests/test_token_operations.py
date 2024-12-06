import pytest
from unittest.mock import patch, MagicMock
from src.token_operations import PumpPortalTrader

class TestPumpPortalTrader:

    @pytest.fixture
    def mock_trader(self):
        trader = PumpPortalTrader()
        trader.signer_keypair = MagicMock()
        trader.mint_keypair = MagicMock()
        return trader

    @patch('requests.post')
    def test_create_token(self, mock_post, mock_trader):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'mock_transaction_data'
        mock_post.return_value = mock_response

        mock_trader.create_ipfs_metadata = MagicMock(return_value='mock_metadata_uri')

        mock_trader.create_token()
        
        mock_post.assert_called_once_with(
            'https://pumpportal.fun/api/trade-local',
            headers={'Content-Type': 'application/json'},
            data=MagicMock()
        )

        print.assert_called_with("Token successfully created.")

    @patch('requests.get')
    def test_get_token_price(self, mock_get, mock_trader):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'price': 1.23}
        mock_get.return_value = mock_response

        price = mock_trader.get_token_price('mock_mint_address')
        assert price == 1.23

        mock_get.assert_called_once_with('https://pumpportal.fun/api/trade-local/price/mock_mint_address')

    @patch('src.token_operations.PumpPortalTrader.get_token_price')
    def test_sol_to_token(self, mock_get_price, mock_trader):
        mock_get_price.return_value = 0.000001  # 1 SOL = 1,000,000 tokens
        sol_amount = 1
        token_amount = mock_trader.sol_to_token(sol_amount, mock_get_price.return_value)
        assert token_amount == 1000000000000  # 1,000,000 tokens with 6 decimals