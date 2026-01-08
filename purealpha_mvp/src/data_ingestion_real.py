"""
Real Data Ingestion - Unified Interface
Координирует все источники данных и предоставляет единый API
"""
from .data_sources import FREDClient, YahooFinanceClient, CoinGeckoClient
from .enhanced_data_sources import EnhancedDataSources
import logging
from typing import Dict, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class RealDataIngestion:
    """
    Unified data ingestion from all verified sources
    
    Sources:
    - FRED (15 parameters, авторитетность 10/10)
    - Yahoo Finance (10 parameters, авторитетность 8/10)
    - CoinGecko (3 parameters, авторитетность 7/10)
    - Derived metrics (40 parameters, calculated from above)
    
    Total: 68-71 parameters
    """
    
    def __init__(self, fred_api_key: str = None):
        """
        Initialize all data sources
        
        Args:
            fred_api_key: Optional FRED API key (or use FRED_API_KEY env var)
        """
        # FRED Client
        try:
            self.fred = FREDClient(api_key=fred_api_key)
            logger.info("✓ FRED Client initialized")
        except Exception as e:
            logger.warning(f"⚠️  FRED Client initialization failed: {e}")
            self.fred = None
        
        # Yahoo Finance Client
        try:
            self.yahoo = YahooFinanceClient()
            logger.info("✓ Yahoo Finance Client initialized")
        except Exception as e:
            logger.warning(f"⚠️  Yahoo Finance Client initialization failed: {e}")
            self.yahoo = None
        
        # CoinGecko Client
        try:
            self.coingecko = CoinGeckoClient()
            logger.info("✓ CoinGecko Client initialized")
        except Exception as e:
            logger.warning(f"⚠️  CoinGecko Client initialization failed: {e}")
            self.coingecko = None
        
        # Enhanced Data Sources (derived metrics)
        self.enhanced = EnhancedDataSources()
        logger.info("✓ Enhanced Data Sources initialized")
        
        # Track last fetch time and results
        self.last_fetch_time = None
        self.last_fetch_data = None
        self.fetch_count = 0
        
        logger.info("Real Data Ingestion initialized")
    
    def fetch_all_parameters(self, use_cache: bool = False, cache_ttl: int = 900) -> Dict:
        """
        Fetch all parameters from all sources
        
        Args:
            use_cache: If True, use cached data if fresh
            cache_ttl: Cache time-to-live in seconds (default: 15 min)
            
        Returns:
            Dictionary of {parameter: value} ready for regime detection
        """
        # Check cache
        if use_cache and self.last_fetch_data and self.last_fetch_time:
            age = (datetime.now() - self.last_fetch_time).total_seconds()
            if age < cache_ttl:
                logger.info(f"Using cached data (age: {age:.0f}s)")
                return self.last_fetch_data
        
        logger.info("=" * 60)
        logger.info("FETCHING REAL MARKET DATA FROM ALL SOURCES")
        logger.info("=" * 60)
        
        all_data = {}
        sources_status = {}
        
        # 1. Fetch from FRED (15 parameters)
        if self.fred:
            try:
                logger.info("\n[1/3] Fetching from FRED...")
                fred_data = self.fred.fetch_all()
                all_data.update(fred_data)
                sources_status['FRED'] = {
                    'success': True,
                    'parameters': len(fred_data),
                    'expected': 15
                }
                logger.info(f"✓ FRED: {len(fred_data)} parameters fetched")
            except Exception as e:
                logger.error(f"✗ FRED fetch failed: {e}")
                sources_status['FRED'] = {'success': False, 'error': str(e)}
        else:
            logger.warning("⊘ FRED client not available")
            sources_status['FRED'] = {'success': False, 'error': 'Client not initialized'}
        
        # 2. Fetch from Yahoo Finance (10 parameters)
        if self.yahoo:
            try:
                logger.info("\n[2/3] Fetching from Yahoo Finance...")
                yahoo_data = self.yahoo.fetch_all()
                all_data.update(yahoo_data)
                
                # Calculate credit spreads
                spreads = self.yahoo.calculate_credit_spreads(yahoo_data)
                all_data.update(spreads)
                
                sources_status['Yahoo Finance'] = {
                    'success': True,
                    'parameters': len(yahoo_data) + len(spreads),
                    'expected': 10
                }
                logger.info(f"✓ Yahoo Finance: {len(yahoo_data)} parameters + {len(spreads)} spreads")
            except Exception as e:
                logger.error(f"✗ Yahoo Finance fetch failed: {e}")
                sources_status['Yahoo Finance'] = {'success': False, 'error': str(e)}
        else:
            logger.warning("⊘ Yahoo Finance client not available")
            sources_status['Yahoo Finance'] = {'success': False, 'error': 'Client not initialized'}
        
        # 3. Fetch from CoinGecko (3 parameters)
        if self.coingecko:
            try:
                logger.info("\n[3/3] Fetching from CoinGecko...")
                crypto_data = self.coingecko.fetch_all()
                stablecoin_data = self.coingecko.fetch_stablecoin_supply()
                
                all_data.update(crypto_data)
                if stablecoin_data.get('stablecoin_supply'):
                    all_data['stablecoin_supply'] = stablecoin_data['stablecoin_supply']
                
                sources_status['CoinGecko'] = {
                    'success': True,
                    'parameters': len(crypto_data) + (1 if stablecoin_data.get('stablecoin_supply') else 0),
                    'expected': 3
                }
                logger.info(f"✓ CoinGecko: {len(crypto_data)} crypto + stablecoin supply")
            except Exception as e:
                logger.error(f"✗ CoinGecko fetch failed: {e}")
                sources_status['CoinGecko'] = {'success': False, 'error': str(e)}
        else:
            logger.warning("⊘ CoinGecko client not available")
            sources_status['CoinGecko'] = {'success': False, 'error': 'Client not initialized'}
        
        # Calculate derived parameters
        derived = self._calculate_derived_parameters(all_data)
        all_data.update(derived)
        
        # Calculate enhanced metrics (40 additional parameters)
        try:
            enhanced = self.enhanced.calculate_derived_parameters(all_data)
            all_data.update(enhanced)
            logger.info(f"✓ Enhanced: {len(enhanced)} derived parameters calculated")
        except Exception as e:
            logger.error(f"Enhanced calculation failed: {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(f"FETCH COMPLETE: {len(all_data)} total parameters")
        logger.info("=" * 60)
        
        for source, status in sources_status.items():
            if status['success']:
                logger.info(f"✓ {source}: {status['parameters']}/{status['expected']} parameters")
            else:
                logger.error(f"✗ {source}: {status.get('error', 'Unknown error')}")
        
        # Update cache
        self.last_fetch_data = all_data
        self.last_fetch_time = datetime.now()
        self.fetch_count += 1
        
        return all_data
    
    def _calculate_derived_parameters(self, data: Dict) -> Dict:
        """
        Calculate derived parameters from fetched data
        
        Examples:
        - Yield curve slope (10Y - 2Y)
        - GDP growth rate (YoY change)
        - Inflation rate (YoY change)
        """
        derived = {}
        
        # Yield curve slope
        if 'treasury_10y' in data and 'treasury_2y' in data:
            slope = data['treasury_10y'] - data['treasury_2y']
            derived['yield_curve_slope'] = slope
            logger.info(f"✓ Derived: Yield curve slope = {slope:.4f}")
        
        # Additional derived parameters can be added here
        # For MVP, keeping it simple
        
        return derived
    
    def validate_data(self, data: Dict) -> tuple:
        """
        Validate fetched data quality
        
        Returns:
            (is_valid: bool, warnings: List[str])
        """
        warnings = []
        
        # 1. Check critical parameters present
        critical_params = [
            'unemployment',
            'vix',
            'fed_funds_rate',
            'dxy'
        ]
        
        missing_critical = [p for p in critical_params if p not in data or data[p] is None]
        if missing_critical:
            warnings.append(f"Missing critical parameters: {missing_critical}")
        
        # 2. Check values in reasonable ranges
        ranges = {
            'vix': (0, 100, "VIX out of reasonable range"),
            'cpi_inflation': (-0.05, 0.20, "CPI inflation out of range"),
            'unemployment': (0, 0.25, "Unemployment rate out of range"),
            'fed_funds_rate': (0, 0.20, "Fed Funds rate out of range"),
            'dxy': (80, 120, "Dollar index out of range"),
            'sp500': (1000, 10000, "S&P500 out of range"),
            'gold_price': (1000, 5000, "Gold price out of range")
        }
        
        for param, (low, high, message) in ranges.items():
            if param in data and data[param] is not None:
                value = data[param]
                if not (low <= value <= high):
                    warnings.append(f"{message}: {value:.2f}")
        
        # 3. Check data freshness
        # (Would need timestamp tracking for each parameter)
        
        # 4. Check minimum parameter count
        min_params = 20  # Should have at least 20 parameters
        if len(data) < min_params:
            warnings.append(f"Only {len(data)} parameters available (expected {min_params}+)")
        
        # Validation result
        is_valid = len(missing_critical) == 0 and len(data) >= min_params
        
        if warnings:
            for warning in warnings:
                logger.warning(f"⚠️  Validation: {warning}")
        else:
            logger.info("✓ Data validation passed")
        
        return is_valid, warnings
    
    def get_fetch_stats(self) -> Dict:
        """Get statistics about data fetching"""
        return {
            'total_fetches': self.fetch_count,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_parameters_count': len(self.last_fetch_data) if self.last_fetch_data else 0,
            'sources_available': {
                'FRED': self.fred is not None,
                'Yahoo Finance': self.yahoo is not None,
                'CoinGecko': self.coingecko is not None
            }
        }
    
    def get_available_parameters(self) -> List[str]:
        """Get list of all available parameters"""
        params = []
        
        if self.fred:
            params.extend(self.fred.SERIES.keys())
        
        if self.yahoo:
            params.extend(self.yahoo.TICKERS.keys())
        
        if self.coingecko:
            params.extend(self.coingecko.COINS.keys())
            params.append('stablecoin_supply')
        
        # Add derived parameters
        params.append('yield_curve_slope')
        
        return sorted(params)
    
    def fetch_historical(self, parameter: str, start_date: str = '2020-01-01'):
        """
        Fetch historical data for a specific parameter
        
        Routes to appropriate client based on parameter
        """
        # Check which client owns this parameter
        if self.fred and parameter in self.fred.SERIES:
            return self.fred.fetch_historical(parameter, start_date)
        
        elif self.yahoo and parameter in self.yahoo.TICKERS:
            return self.yahoo.fetch_historical(parameter, start_date)
        
        elif self.coingecko and parameter in self.coingecko.COINS:
            days = (datetime.now() - datetime.fromisoformat(start_date)).days
            return self.coingecko.fetch_historical(parameter, days=days)
        
        else:
            raise ValueError(f"Unknown parameter: {parameter}")
