"""
FRED (Federal Reserve Economic Data) Client
Источник: Федеральная резервная система США
Авторитетность: 10/10
Стоимость: Бесплатно
"""
import pandas as pd
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class FREDClient:
    """
    Client for Federal Reserve Economic Data
    
    Provides 15 macro parameters from official Fed sources
    """
    
    # Mapping параметров к FRED series IDs
    SERIES = {
        # GDP & Growth (3)
        'gdp_growth': {
            'series_id': 'GDP',
            'name': 'Gross Domestic Product',
            'frequency': 'quarterly',
            'unit': 'billions_usd'
        },
        'gdp_real': {
            'series_id': 'GDPC1',
            'name': 'Real GDP',
            'frequency': 'quarterly',
            'unit': 'billions_2017_usd'
        },
        
        # Inflation (2)
        'cpi_inflation': {
            'series_id': 'CPIAUCSL',
            'name': 'Consumer Price Index',
            'frequency': 'monthly',
            'unit': 'index_1982_84=100'
        },
        'pce_inflation': {
            'series_id': 'PCEPI',
            'name': 'Personal Consumption Expenditures Price Index',
            'frequency': 'monthly',
            'unit': 'index_2017=100'
        },
        
        # Labor Market (1)
        'unemployment': {
            'series_id': 'UNRATE',
            'name': 'Unemployment Rate',
            'frequency': 'monthly',
            'unit': 'percent'
        },
        
        # Interest Rates (4)
        'fed_funds_rate': {
            'series_id': 'FEDFUNDS',
            'name': 'Federal Funds Effective Rate',
            'frequency': 'monthly',
            'unit': 'percent'
        },
        'treasury_10y': {
            'series_id': 'GS10',
            'name': '10-Year Treasury Constant Maturity Rate',
            'frequency': 'daily',
            'unit': 'percent'
        },
        'treasury_2y': {
            'series_id': 'GS2',
            'name': '2-Year Treasury Constant Maturity Rate',
            'frequency': 'daily',
            'unit': 'percent'
        },
        'treasury_30y': {
            'series_id': 'GS30',
            'name': '30-Year Treasury Constant Maturity Rate',
            'frequency': 'daily',
            'unit': 'percent'
        },
        
        # Money Supply & Fed (2)
        'm2_money_supply': {
            'series_id': 'M2SL',
            'name': 'M2 Money Stock',
            'frequency': 'weekly',
            'unit': 'billions_usd'
        },
        'fed_balance_sheet': {
            'series_id': 'WALCL',
            'name': 'Federal Reserve Total Assets',
            'frequency': 'weekly',
            'unit': 'millions_usd'
        },
        
        # Economic Activity (3)
        'retail_sales': {
            'series_id': 'RSXFS',
            'name': 'Retail Sales',
            'frequency': 'monthly',
            'unit': 'millions_usd'
        },
        'industrial_production': {
            'series_id': 'INDPRO',
            'name': 'Industrial Production Index',
            'frequency': 'monthly',
            'unit': 'index_2017=100'
        },
        'housing_starts': {
            'series_id': 'HOUST',
            'name': 'Housing Starts',
            'frequency': 'monthly',
            'unit': 'thousands_units'
        }
    }
    
    def __init__(self, api_key: str = None):
        """
        Initialize FRED client
        
        Args:
            api_key: FRED API key (get free at https://fred.stlouisfed.org/docs/api/api_key.html)
        """
        if api_key is None:
            api_key = os.getenv('FRED_API_KEY')
        
        if not api_key:
            logger.warning("No FRED API key provided - using fallback method")
            self.api_key = None
            self.use_fallback = True
        else:
            self.api_key = api_key
            self.use_fallback = False
            
        logger.info(f"FRED Client initialized (fallback mode: {self.use_fallback})")
    
    def fetch_latest(self, parameter: str) -> dict:
        """
        Fetch latest value for parameter
        
        Args:
            parameter: Parameter name from SERIES dict
            
        Returns:
            {
                'parameter': str,
                'value': float,
                'timestamp': datetime,
                'source': 'FRED',
                'series_id': str,
                'frequency': str
            }
        """
        if parameter not in self.SERIES:
            raise ValueError(f"Unknown parameter: {parameter}. Available: {list(self.SERIES.keys())}")
        
        series_info = self.SERIES[parameter]
        series_id = series_info['series_id']
        
        try:
            if self.use_fallback:
                # Fallback: use pandas_datareader
                return self._fetch_fallback(parameter, series_info)
            else:
                # Use fredapi
                return self._fetch_with_api(parameter, series_info)
                
        except Exception as e:
            logger.error(f"Failed to fetch {parameter}: {e}")
            return {
                'parameter': parameter,
                'value': None,
                'error': str(e),
                'source': 'FRED',
                'series_id': series_id
            }
    
    def _fetch_with_api(self, parameter: str, series_info: dict) -> dict:
        """Fetch using fredapi library"""
        try:
            from fredapi import Fred
        except ImportError:
            logger.warning("fredapi not installed, falling back to pandas_datareader")
            return self._fetch_fallback(parameter, series_info)
        
        fred = Fred(api_key=self.api_key)
        series_id = series_info['series_id']
        
        # Fetch latest release
        series = fred.get_series_latest_release(series_id)
        
        # Get most recent value
        latest_value = float(series.iloc[-1])
        latest_date = series.index[-1]
        
        # Convert to appropriate units if needed
        value = self._convert_units(parameter, latest_value, series_info)
        
        result = {
            'parameter': parameter,
            'value': value,
            'timestamp': latest_date,
            'source': 'FRED',
            'series_id': series_id,
            'frequency': series_info['frequency'],
            'name': series_info['name']
        }
        
        logger.info(f"✓ {parameter}: {value:.4f} ({latest_date.strftime('%Y-%m-%d')})")
        
        return result
    
    def _fetch_fallback(self, parameter: str, series_info: dict) -> dict:
        """Fallback using pandas_datareader"""
        try:
            import pandas_datareader as pdr
        except ImportError:
            raise ImportError("Neither fredapi nor pandas_datareader installed. Install with: pip install fredapi pandas-datareader")
        
        series_id = series_info['series_id']
        
        # Fetch from FRED via pandas_datareader
        df = pdr.DataReader(series_id, 'fred', start='2020-01-01')
        
        if df.empty:
            raise ValueError(f"No data returned for {series_id}")
        
        # Get most recent value
        latest_value = float(df.iloc[-1, 0])
        latest_date = df.index[-1]
        
        # Convert to appropriate units
        value = self._convert_units(parameter, latest_value, series_info)
        
        result = {
            'parameter': parameter,
            'value': value,
            'timestamp': latest_date,
            'source': 'FRED',
            'series_id': series_id,
            'frequency': series_info['frequency'],
            'name': series_info['name']
        }
        
        logger.info(f"✓ {parameter}: {value:.4f} ({latest_date.strftime('%Y-%m-%d')})")
        
        return result
    
    def _convert_units(self, parameter: str, value: float, series_info: dict) -> float:
        """
        Convert values to standardized units
        
        Examples:
        - Percentages: keep as decimal (0.05 = 5%)
        - GDP: billions USD
        - Rates: decimal (0.05 = 5%)
        """
        unit = series_info['unit']
        
        # Interest rates and percentages: convert to decimal
        if 'percent' in unit:
            return value / 100.0  # 5% -> 0.05
        
        # GDP growth rate calculation
        if parameter == 'gdp_growth':
            # Calculate YoY growth rate (would need historical data)
            # For now, return as-is (billions USD)
            return value / 1000000  # Normalize to trillions for readability
        
        # Default: return as-is
        return value
    
    def fetch_all(self) -> dict:
        """
        Fetch all available parameters
        
        Returns:
            Dictionary of {parameter: value}
        """
        results = {}
        errors = []
        
        for parameter in self.SERIES.keys():
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
        total_count = len(self.SERIES)
        
        logger.info(f"FRED: Fetched {success_count}/{total_count} parameters")
        
        if errors:
            logger.warning(f"FRED: Failed parameters: {errors}")
        
        return results
    
    def fetch_historical(self, parameter: str, start_date: str = '2020-01-01') -> pd.DataFrame:
        """
        Fetch historical data for backtesting
        
        Args:
            parameter: Parameter name
            start_date: Start date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical values
        """
        if parameter not in self.SERIES:
            raise ValueError(f"Unknown parameter: {parameter}")
        
        series_info = self.SERIES[parameter]
        series_id = series_info['series_id']
        
        try:
            if self.use_fallback:
                import pandas_datareader as pdr
                df = pdr.DataReader(series_id, 'fred', start=start_date)
            else:
                from fredapi import Fred
                fred = Fred(api_key=self.api_key)
                series = fred.get_series(series_id, observation_start=start_date)
                df = series.to_frame(name='value')
            
            logger.info(f"Fetched {len(df)} historical points for {parameter}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {parameter}: {e}")
            return pd.DataFrame()
    
    def get_parameter_info(self, parameter: str = None) -> dict:
        """Get information about available parameters"""
        if parameter:
            if parameter not in self.SERIES:
                raise ValueError(f"Unknown parameter: {parameter}")
            return self.SERIES[parameter]
        else:
            return self.SERIES
