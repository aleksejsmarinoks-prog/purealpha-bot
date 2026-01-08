"""
Pytest configuration and fixtures
"""
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'gdp_growth': 0.025,
        'inflation': 0.028,
        'unemployment': 0.041,
        'vix': 22.5,
        'fed_rate': 0.055,
        'credit_spread': 0.0145,
        'dxy': 104.2
    }

@pytest.fixture
def sample_time_series():
    """Sample time series data for causal tests"""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    
    # Create causal relationship: X causes Y with lag 1
    X = np.random.randn(100).cumsum()
    Y = 0.8 * np.roll(X, 1) + np.random.randn(100) * 0.2
    Y[0] = np.random.randn()
    
    return pd.DataFrame({'X': X, 'Y': Y}, index=dates)
