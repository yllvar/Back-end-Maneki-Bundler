import requests
import base58
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from .token_operations import PumpPortalTrader
from . import config

def create_jito_bundle():
    trader = PumpPortalTrader()
    signer_keypairs = [Keypair.from_base58_string(key) for key in config.PRIVATE_KEYS]
    mint_keypair = trader.mint_keypair

    metadata_uri = trader.create_ipfs_metadata()
    token_metadata = {
        'name': config.TOKEN_METADATA['name'],
        'symbol': config.TOKEN_METADATA['symbol'],
        'uri': metadata_uri
    }

    # Get the token price to convert SOL to tokens
    token_price = trader.get_token_price(mint_keypair.pubkey())
    sol_allocated = 1  # Example: 1 SOL per wallet
    token_amount = trader.sol_to_token(sol_allocated, token_price)

    bundled_transaction_args = [
        {
            'publicKey': str(signer_keypairs[0].pubkey()),
            'action': 'create',
            'tokenMetadata': token_metadata,
            'mint': str(mint_keypair.pubkey()),
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
                "mint": str(mint_keypair.pubkey()), 
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