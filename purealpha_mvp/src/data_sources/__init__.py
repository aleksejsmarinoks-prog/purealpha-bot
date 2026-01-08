"""
Data Sources Module
Clients for fetching real market data
"""

from .fred_client import FREDClient
from .yahoo_client import YahooFinanceClient
from .coingecko_client import CoinGeckoClient

__all__ = ['FREDClient', 'YahooFinanceClient', 'CoinGeckoClient']
