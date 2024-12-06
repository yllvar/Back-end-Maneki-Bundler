import requests
import json
import base58
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig
from solders.rpc.requests import SendVersionedTransaction
from solders.commitment_config import CommitmentLevel
from . import config

class PumpPortalTrader:
    def __init__(self):
        self.signer_keypair = Keypair.from_base58_string('your-base58-private-key')
        self.mint_keypair = Keypair()

    def create_ipfs_metadata(self):
        with open(config.IMAGE_PATH, 'rb') as f:
            file_content = f.read()

        files = {'file': ('example.png', file_content, 'image/png')}
        metadata_response = requests.post("https://pump.fun/api/ipfs", data=config.TOKEN_METADATA, files=files)
        return metadata_response.json()['metadataUri']

    def create_token(self):
        metadata_uri = self.create_ipfs_metadata()
        token_metadata = {
            'name': config.TOKEN_METADATA['name'],
            'symbol': config.TOKEN_METADATA['symbol'],
            'uri': metadata_uri
        }

        response = requests.post(
            config.PUMPPORTAL_API,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'publicKey': str(self.signer_keypair.pubkey()),
                'action': 'create',
                'tokenMetadata': token_metadata,
                'mint': str(self.mint_keypair.pubkey()),
                'denominatedInSol': 'true',
                'amount': 1,  # Dev buy of 1 SOL
                'slippage': 10,
                'priorityFee': 0.0005,
                'pool': 'pump'
            })
        )

        if response.status_code == 200:
            print("Token successfully created.")
        else:
            print(f"Token creation failed: {response.text}")
            return

        tx = VersionedTransaction(VersionedTransaction.from_bytes(response.content).message, [self.mint_keypair, self.signer_keypair])
        commitment = CommitmentLevel.Confirmed
        config = RpcSendTransactionConfig(preflight_commitment=commitment)
        txPayload = SendVersionedTransaction(tx, config)

        response = requests.post(
            config.RPC_ENDPOINT,
            headers={"Content-Type": "application/json"},
            data=txPayload.to_json()
        )
        tx_signature = response.json().get('result')
        print(f'Transaction: https://solscan.io/tx/{tx_signature}')

    def get_token_price(self, mint):
        """Fetch the current token price based on the bonding curve."""
        response = requests.get(f"{config.PUMPPORTAL_API}/price/{mint}")
        if response.status_code == 200:
            return response.json().get('price')
        else:
            raise ValueError("Failed to fetch token price.")

    def sol_to_token(self, sol_amount, token_price):
        """Convert SOL amount to token amount based on price."""
        return int((sol_amount * 10**config.SOL_DECIMALS) / token_price)

    def send_create_tx_bundle(self):
        signer_keypairs = [Keypair.from_base58_string(key) for key in config.PRIVATE_KEYS]
        metadata_uri = self.create_ipfs_metadata()
        token_metadata = {
            'name': config.TOKEN_METADATA['name'],
            'symbol': config.TOKEN_METADATA['symbol'],
            'uri': metadata_uri
        }

        # Get the token price to convert SOL to tokens
        token_price = self.get_token_price(self.mint_keypair.pubkey())
        sol_allocated = 1  # Example: 1 SOL per wallet
        token_amount = self.sol_to_token(sol_allocated, token_price)

        bundled_transaction_args = [
            {
                'publicKey': str(signer_keypairs[0].pubkey()),
                'action': 'create',
                'tokenMetadata': token_metadata,
                'mint': str(self.mint_keypair.pubkey()),
                'denominatedInSol': 'false',
                'amount': token_amount,
                'slippage': 10,
                'priorityFee': 0.0005,
                'pool': 'pump'
            },
            *[
                {
                    "publicKey": str(keypair.pubkey()),
                    "action": "buy",
                    "mint": str(self.mint_keypair.pubkey()),
                    "denominatedInSol": "false",
                    "amount": token_amount,
                    "slippage": 50,
                    "priorityFee": 0.0001,
                    "pool": "pump"
                }
                for keypair in signer_keypairs[1:]
            ]
        ]

        response = requests.post(
            config.PUMPPORTAL_API,
            headers={"Content-Type": "application/json"},
            json=bundled_transaction_args
        )

        if response.status_code != 200:
            print("Failed to generate transactions.")
            print(response.reason)
        else:
            encoded_transactions = response.json()
            signed_encoded_transactions = []

            for index, encoded_transaction in enumerate(encoded_transactions):
                keypair = signer_keypairs[index]
                signed_tx = VersionedTransaction(VersionedTransaction.from_bytes(base58.b58decode(encoded_transaction)).message, [keypair])
                signed_encoded_transactions.append(base58.b58encode(bytes(signed_tx)).decode())

            # Send Jito Bundle
            jito_response = requests.post(
                config.JITO_BUNDLE_API,
                headers={"Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendBundle",
                    "params": {"transactions": signed_encoded_transactions}
                }
            )

            if jito_response.status_code == 200:
                print("Jito bundle successfully executed.")
            else:
                print("Failed to execute Jito bundle.")
                print(jito_response.text)