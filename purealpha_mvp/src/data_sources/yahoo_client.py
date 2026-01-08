"""
Yahoo Finance Client
Источник: Биржевые данные (NYSE, NASDAQ, commodities)
Авторитетность: 8/10
Стоимость: Бесплатно
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YahooFinanceClient:
    """
    Client for Yahoo Finance market data
    
    Provides 10 market parameters from exchange data
    """
    
    # Mapping параметров к Yahoo tickers
    TICKERS = {
        # Volatility & Indices (4)
        'vix': {
            'ticker': '^VIX',
            'name': 'CBOE Volatility Index',
            'type': 'index',
            'description': 'Market fear gauge'
        },
        'sp500': {
            'ticker': '^GSPC',
            'name': 'S&P 500',
            'type': 'index',
            'description': 'US large-cap index'
        },
        'nasdaq': {
            'ticker': '^IXIC',
            'name': 'NASDAQ Composite',
            'type': 'index',
            'description': 'Tech-heavy index'
        },
        'russell_2000': {
            'ticker': '^RUT',
            'name': 'Russell 2000',
            'type': 'index',
            'description': 'Small-cap index'
        },
        
        # FX & Commodities (4)
        'dxy': {
            'ticker': 'DX-Y.NYB',
            'name': 'US Dollar Index',
            'type': 'currency',
            'description': 'Dollar vs basket of currencies'
        },
        'gold_price': {
            'ticker': 'GC=F',
            'name': 'Gold Futures',
            'type': 'commodity',
            'description': 'Gold price per troy ounce'
        },
        'oil_wti': {
            'ticker': 'CL=F',
            'name': 'Crude Oil WTI Futures',
            'type': 'commodity',
            'description': 'West Texas Intermediate crude'
        },
        'copper': {
            'ticker': 'HG=F',
            'name': 'Copper Futures',
            'type': 'commodity',
            'description': 'Industrial metal indicator'
        },
        
        # Bond ETFs (для credit spread calculation) (2)
        'lqd_price': {
            'ticker': 'LQD',
            'name': 'iShares iBoxx Investment Grade Corp Bond ETF',
            'type': 'etf',
            'description': 'Investment grade corporate bonds'
        },
        'hyg_price': {
            'ticker': 'HYG',
            'name': 'iShares iBoxx High Yield Corp Bond ETF',
            'type': 'etf',
            'description': 'High yield corporate bonds'
        }
    }
    
    def __init__(self):
        """Initialize Yahoo Finance client"""
        logger.info("Yahoo Finance Client initialized")
    
    def fetch_latest(self, parameter: str) -> dict:
        """
        Fetch latest price for parameter
        
        Args:
            parameter: Parameter name from TICKERS dict
            
        Returns:
            {
                'parameter': str,
                'value': float,
                'timestamp': datetime,
                'source': 'Yahoo Finance',
                'ticker': str
            }
        """
        if parameter not in self.TICKERS:
            raise ValueError(f"Unknown parameter: {parameter}. Available: {list(self.TICKERS.keys())}")
        
        ticker_info = self.TICKERS[parameter]
        ticker = ticker_info['ticker']
        
        try:
            # Fetch recent data (2 days to ensure we get latest)
            data = yf.download(ticker, period='2d', progress=False, show_errors=False)
            
            if data.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # Get most recent close price
            latest_value = float(data['Close'].iloc[-1])
            latest_date = data.index[-1]
            
            result = {
                'parameter': parameter,
                'value': latest_value,
                'timestamp': latest_date,
                'source': 'Yahoo Finance',
                'ticker': ticker,
                'name': ticker_info['name'],
                'type': ticker_info['type']
            }
            
            logger.info(f"✓ {parameter}: {latest_value:.2f} ({latest_date.strftime('%Y-%m-%d')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch {parameter} ({ticker}): {e}")
            return {
                'parameter': parameter,
                'value': None,
                'error': str(e),
                'source': 'Yahoo Finance',
                'ticker': ticker
            }
    
    def fetch_all(self) -> dict:
        """
        Fetch all available parameters
        
        Returns:
            Dictionary of {parameter: value}
        """
        results = {}
        errors = []
        
        for parameter in self.TICKERS.keys():
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
        total_count = len(self.TICKERS)
        
        logger.info(f"Yahoo Finance: Fetched {success_count}/{total_count} parameters")
        
        if errors:
            logger.warning(f"Yahoo Finance: Failed parameters: {errors}")
        
        return results
    
    def calculate_credit_spreads(self, data: dict) -> dict:
        """
        Calculate credit spreads from bond ETF prices
        
        Note: This is a simplified calculation using price changes as proxy.
        For production, would need actual yield data.
        
        Args:
            data: Dictionary containing lqd_price, hyg_price
            
        Returns:
            Dictionary with credit spread estimates
        """
        spreads = {}
        
        # Investment Grade spread (simplified)
        if 'lqd_price' in data:
            # Rough proxy: assume inverse relationship between price and yield
            # Lower prices = higher yields = wider spreads
            # This is placeholder logic for MVP
            lqd_price = data['lqd_price']
            
            # Normalized spread estimate (would need yield data for accuracy)
            # Assuming LQD typical price range 100-120
            spread_estimate = max(0.01, 0.05 - (lqd_price - 100) * 0.001)
            spreads['ig_credit_spread'] = spread_estimate
            
            logger.info(f"✓ IG Credit Spread (estimate): {spread_estimate:.4f}")
        
        # High Yield spread (simplified)
        if 'hyg_price' in data:
            hyg_price = data['hyg_price']
            
            # HY spreads typically 3-5% above IG
            # Assuming HYG typical price range 75-85
            spread_estimate = max(0.03, 0.08 - (hyg_price - 75) * 0.002)
            spreads['hy_credit_spread'] = spread_estimate
            
            logger.info(f"✓ HY Credit Spread (estimate): {spread_estimate:.4f}")
        
        if not spreads:
            logger.warning("Could not calculate credit spreads - missing bond ETF data")
        else:
            logger.info("⚠️  Credit spreads are estimates - production needs yield data")
        
        return spreads
    
    def fetch_historical(self, parameter: str, start_date: str = '2020-01-01') -> pd.DataFrame:
        """
        Fetch historical data for backtesting
        
        Args:
            parameter: Parameter name
            start_date: Start date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical prices
        """
        if parameter not in self.TICKERS:
            raise ValueError(f"Unknown parameter: {parameter}")
        
        ticker_info = self.TICKERS[parameter]
        ticker = ticker_info['ticker']
        
        try:
            # Fetch historical data
            data = yf.download(ticker, start=start_date, progress=False, show_errors=False)
            
            if data.empty:
                raise ValueError(f"No historical data for {ticker}")
            
            logger.info(f"Fetched {len(data)} historical points for {parameter}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {parameter}: {e}")
            return pd.DataFrame()
    
    def get_parameter_info(self, parameter: str = None) -> dict:
        """Get information about available parameters"""
        if parameter:
            if parameter not in self.TICKERS:
                raise ValueError(f"Unknown parameter: {parameter}")
            return self.TICKERS[parameter]
        else:
            return self.TICKERS
