"""
CoinGecko Client
Источник: Агрегатор криптобирж
Авторитетность: 7/10
Стоимость: Бесплатно (50 calls/min limit)
"""
import requests
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

class CoinGeckoClient:
    """
    Client for cryptocurrency market data
    
    Provides 3 crypto parameters from CoinGecko API
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Mapping параметров к CoinGecko IDs
    COINS = {
        'btc_price': {
            'coin_id': 'bitcoin',
            'name': 'Bitcoin',
            'symbol': 'BTC',
            'description': 'Leading cryptocurrency'
        },
        'eth_price': {
            'coin_id': 'ethereum',
            'name': 'Ethereum',
            'symbol': 'ETH',
            'description': 'Smart contract platform'
        }
    }
    
    # Stablecoins для supply tracking
    STABLECOINS = {
        'usdt': {
            'coin_id': 'tether',
            'name': 'Tether',
            'symbol': 'USDT'
        },
        'usdc': {
            'coin_id': 'usd-coin',
            'name': 'USD Coin',
            'symbol': 'USDC'
        }
    }
    
    def __init__(self):
        """Initialize CoinGecko client"""
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Rate limit: 50 calls/min = 1.2s between calls
        logger.info("CoinGecko Client initialized")
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch_latest(self, parameter: str) -> dict:
        """
        Fetch latest crypto price
        
        Args:
            parameter: Parameter name from COINS dict
            
        Returns:
            {
                'parameter': str,
                'value': float,
                'timestamp': datetime,
                'source': 'CoinGecko',
                'coin_id': str
            }
        """
        if parameter not in self.COINS:
            raise ValueError(f"Unknown parameter: {parameter}. Available: {list(self.COINS.keys())}")
        
        coin_info = self.COINS[parameter]
        coin_id = coin_info['coin_id']
        
        try:
            # Rate limiting
            self._rate_limit()
            
            # Call API
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if coin_id not in data:
                raise ValueError(f"No data returned for {coin_id}")
            
            coin_data = data[coin_id]
            price = coin_data['usd']
            
            result = {
                'parameter': parameter,
                'value': float(price),
                'timestamp': datetime.now(),
                'source': 'CoinGecko',
                'coin_id': coin_id,
                'name': coin_info['name'],
                'symbol': coin_info['symbol'],
                'market_cap': coin_data.get('usd_market_cap'),
                'volume_24h': coin_data.get('usd_24h_vol'),
                'change_24h': coin_data.get('usd_24h_change')
            }
            
            logger.info(f"✓ {parameter}: ${price:,.2f} ({coin_info['symbol']})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch {parameter} ({coin_id}): {e}")
            return {
                'parameter': parameter,
                'value': None,
                'error': str(e),
                'source': 'CoinGecko',
                'coin_id': coin_id
            }
    
    def fetch_all(self) -> dict:
        """
        Fetch all available parameters
        
        Returns:
            Dictionary of {parameter: value}
        """
        results = {}
        errors = []
        
        for parameter in self.COINS.keys():
            try:
                data = self.fetch_latest(parameter)
                if data['value'] is not None:
                    results[parameter] = data['value']
                else:
                    errors.append(parameter)
            except Exception as e:
                logger.error(f"Failed to fetch {parameter}: {e}")
                errors.append(parameter)
        
        success_count = len(results)
        total_count = len(self.COINS)
        
        logger.info(f"CoinGecko: Fetched {success_count}/{total_count} parameters")
        
        if errors:
            logger.warning(f"CoinGecko: Failed parameters: {errors}")
        
        return results
    
    def fetch_stablecoin_supply(self) -> dict:
        """
        Fetch total stablecoin supply (USDT + USDC)
        
        Returns:
            {
                'stablecoin_supply': float (total market cap in USD),
                'usdt_supply': float,
                'usdc_supply': float,
                'timestamp': datetime
            }
        """
        try:
            # Rate limiting
            self._rate_limit()
            
            # Fetch market data for stablecoins
            url = f"{self.BASE_URL}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': ','.join([info['coin_id'] for info in self.STABLECOINS.values()]),
                'order': 'market_cap_desc'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                raise ValueError("No stablecoin data returned")
            
            # Extract market caps
            supplies = {}
            total_supply = 0
            
            for coin_data in data:
                coin_id = coin_data['id']
                market_cap = coin_data['market_cap']
                
                # Map coin_id to our keys
                for key, info in self.STABLECOINS.items():
                    if info['coin_id'] == coin_id:
                        supplies[f'{key}_supply'] = market_cap
                        total_supply += market_cap
                        break
            
            result = {
                'stablecoin_supply': total_supply,
                **supplies,
                'timestamp': datetime.now(),
                'source': 'CoinGecko'
            }
            
            logger.info(f"✓ Stablecoin Supply: ${total_supply:,.0f} (USDT + USDC)")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch stablecoin supply: {e}")
            return {
                'stablecoin_supply': None,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def fetch_historical(self, parameter: str, days: int = 90) -> dict:
        """
        Fetch historical price data
        
        Args:
            parameter: Parameter name
            days: Number of days of history
            
        Returns:
            Dictionary with historical prices
        """
        if parameter not in self.COINS:
            raise ValueError(f"Unknown parameter: {parameter}")
        
        coin_info = self.COINS[parameter]
        coin_id = coin_info['coin_id']
        
        try:
            # Rate limiting
            self._rate_limit()
            
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'prices' not in data:
                raise ValueError(f"No price data for {coin_id}")
            
            # Convert to list of {date, price}
            prices = [
                {
                    'timestamp': datetime.fromtimestamp(p[0] / 1000),
                    'price': p[1]
                }
                for p in data['prices']
            ]
            
            logger.info(f"Fetched {len(prices)} historical points for {parameter}")
            
            return {
                'parameter': parameter,
                'coin_id': coin_id,
                'prices': prices,
                'source': 'CoinGecko'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {parameter}: {e}")
            return {
                'parameter': parameter,
                'prices': [],
                'error': str(e)
            }
    
    def get_parameter_info(self, parameter: str = None) -> dict:
        """Get information about available parameters"""
        if parameter:
            if parameter not in self.COINS:
                raise ValueError(f"Unknown parameter: {parameter}")
            return self.COINS[parameter]
        else:
            return {**self.COINS, **self.STABLECOINS}
