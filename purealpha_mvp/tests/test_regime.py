"""
Tests for Regime Detection Engine
"""
import pytest
import sys
sys.path.insert(0, '/home/claude/purealpha_mvp')
from src.regime_detection import RegimeDetector

def test_goldilocks_detection(sample_market_data):
    """Test GOLDILOCKS regime detection"""
    detector = RegimeDetector()
    result = detector.detect_regime(sample_market_data)
    
    assert result['regime'] == 'GOLDILOCKS'
    assert result['confidence'] > 0.5
    assert 'allocation' in result
    assert result['expected_return'] > 0

def test_lsi_calculation(sample_market_data):
    """Test LSI calculation"""
    detector = RegimeDetector()
    lsi_result = detector.calculate_lsi(sample_market_data)
    
    assert 0 <= lsi_result['lsi'] <= 100
    assert lsi_result['status'] in ['NORMAL', 'MODERATE_STRESS', 'SEVERE_STRESS', 'CRITICAL_LIQUIDITY_SHOCK']
    assert 'components' in lsi_result
