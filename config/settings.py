import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    # Telegram settings
    _admin_env = os.getenv("ADMIN_CHAT_IDS") or os.getenv("ADMIN_CHAT_ID") or ""
    ADMIN_CHAT_IDS = [int(x.strip()) for x in _admin_env.split(",") if x.strip()]
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "TimRobbyPR")

    # Server settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./p2p_bot.db")  # Default to SQLite for easy development
    PORT = int(os.getenv("PORT", 8000))

    # GoPay / Gopiz API Gateway
    GOPAY_GATEWAY_URL = os.getenv("GOPAY_GATEWAY_URL", "http://127.0.0.1:3005")
    GOPAY_API_KEY = os.getenv("GOPAY_API_KEY", "RAHASIA")

    # Wallets & RPC Endpoints
    EVM_PRIVATE_KEY = os.getenv("EVM_PRIVATE_KEY")
    EVM_WALLET_ADDRESS = os.getenv("EVM_WALLET_ADDRESS")
    
    # EVM RPC Endpoints
    BSC_RPC = os.getenv("BSC_RPC", "https://bsc-rpc.publicnode.com")
    ETH_RPC = os.getenv("ETH_RPC", "https://ethereum-rpc.publicnode.com")
    AVAX_RPC = os.getenv("AVAX_RPC", "https://avalanche-c-chain-rpc.publicnode.com")
    POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-bor-rpc.publicnode.com")
    BASE_RPC = os.getenv("BASE_RPC", "https://base-rpc.publicnode.com")
    ARB_RPC = os.getenv("ARB_RPC", "https://arbitrum-one-rpc.publicnode.com")
    OPTIMISM_RPC = os.getenv("OPTIMISM_RPC", "https://optimism-rpc.publicnode.com")
    ROBINHOOD_RPC = os.getenv("ROBINHOOD_RPC", "https://rpc.robinhood.com")
    KAIA_RPC = os.getenv("KAIA_RPC", "https://klaytn.drpc.org")
    BERA_RPC = os.getenv("BERA_RPC", "https://berachain.drpc.org")
    HYPEREVM_RPC = os.getenv("HYPEREVM_RPC", "https://rpc.hyperliquid.xyz/evm")
    GRAVITY_RPC = os.getenv("GRAVITY_RPC", "https://rpc.gravity.xyz")

    # Non-EVM RPCs & Wallets
    SOL_PRIVATE_KEY = os.getenv("SOL_PRIVATE_KEY")
    SOL_WALLET_ADDRESS = os.getenv("SOL_WALLET_ADDRESS")

    TRX_PRIVATE_KEY = os.getenv("TRX_PRIVATE_KEY")
    TRX_WALLET_ADDRESS = os.getenv("TRX_WALLET_ADDRESS")

    TON_RPC = os.getenv("TON_RPC", "https://toncenter.com/api/v2/jsonRPC")
    TON_API_KEY = os.getenv("TON_API_KEY")
    TON_WALLET_ADDRESS = os.getenv("TON_WALLET_ADDRESS")
    TON_PRIVATE_KEY = os.getenv("TON_PRIVATE_KEY")

    SUI_RPC = os.getenv("SUI_RPC", "https://fullnode.mainnet.sui.io:443")
    SUI_WALLET_ADDRESS = os.getenv("SUI_WALLET_ADDRESS")

    APTOS_RPC = os.getenv("APTOS_RPC", "https://fullnode.mainnet.aptos.labs.com/v1")
    APTOS_WALLET_ADDRESS = os.getenv("APTOS_WALLET_ADDRESS")

    # Business Rules
    ORDER_EXPIRE_MINUTES = int(os.getenv("ORDER_EXPIRE_MINUTES", 30))
    DEFAULT_SPREAD_PCT = float(os.getenv("DEFAULT_SPREAD_PCT", 0.0))
    ENABLE_LOW_BALANCE_ALERT = os.getenv("ENABLE_LOW_BALANCE_ALERT", "true").lower() in ("true", "1", "yes")
    LOW_BALANCE_ALERT_HOURS = int(os.getenv("LOW_BALANCE_ALERT_HOURS", 6))

settings = Settings()

