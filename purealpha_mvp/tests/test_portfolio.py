"""
Tests for Portfolio Builder
"""
import pytest
import sys
sys.path.insert(0, '/home/claude/purealpha_mvp')
from src.portfolio_builder import PortfolioBuilder

def test_portfolio_construction():
    """Test portfolio construction"""
    builder = PortfolioBuilder()
    
    regime_allocation = {
        'equities': 0.70,
        'bonds': 0.20,
        'gold': 0.10
    }
    
    portfolio = builder.build_portfolio(
        capital=5000,
        risk_level='MEDIUM',
        regime_allocation=regime_allocation
    )
    
    # Check allocations sum to capital
    total = sum(portfolio['allocations'].values())
    assert abs(total - 5000) < 0.01
    
    # Check metrics exist
    assert 'expected_return' in portfolio['metrics']
    assert 'volatility' in portfolio['metrics']
    assert 'sharpe_ratio' in portfolio['metrics']

def test_normalization():
    """Test allocation normalization"""
    builder = PortfolioBuilder()
    
    raw = {'VTI': 2100.33, 'VXUS': 1400.22, 'BND': 1000.11, 'GLD': 500.05}
    normalized = builder._normalize_allocations(raw, 5000.00)
    
    total = sum(normalized.values())
    assert abs(total - 5000.00) < 0.01
