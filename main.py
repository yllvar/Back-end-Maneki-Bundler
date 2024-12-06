from src.token_operations import PumpPortalTrader

def main():
    trader = PumpPortalTrader()
    trader.create_token()
    trader.send_create_tx_bundle()

if __name__ == "__main__":
    main()