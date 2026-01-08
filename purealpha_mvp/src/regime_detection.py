"""
Regime Detection Engine
Classifies market state into 10 distinct regimes
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects current market regime from 10 defined states
    """
    
    def __init__(self):
        self.regimes = self._define_regimes()
        logger.info(f"Initialized Regime Detector with {len(self.regimes)} regimes")
    
    def _define_regimes(self) -> Dict:
        """
        Defines all 10 market regimes with conditions and allocations
        """
        return {
            'GOLDILOCKS': {
                'conditions': {
                    'gdp_growth': (0.02, 0.05),
                    'inflation': (0.015, 0.030),
                    'vix': (10, 20),
                    'unemployment': (0.03, 0.05)
                },
                'allocation': {
                    'equities': 0.70,
                    'bonds': 0.20,
                    'gold': 0.10
                },
                'expected_return': 0.12,
                'max_drawdown': -0.15,
                'description': 'Moderate growth with stable inflation'
            },
            
            'RECESSION': {
                'conditions': {
                    'gdp_growth': (-0.05, 0.01),
                    'unemployment': (0.06, 0.12),
                    'vix': (25, 50),
                    'credit_spread': (0.03, 0.10)
                },
                'allocation': {
                    'equities': 0.30,
                    'bonds': 0.50,
                    'gold': 0.10,
                    'cash': 0.10
                },
                'expected_return': 0.04,
                'max_drawdown': -0.25,
                'description': 'Economic contraction'
            },
            
            'CRISIS': {
                'conditions': {
                    'vix': (40, 90),
                    'credit_spread': (0.05, 0.20),
                    'unemployment': (0.08, 0.15)
                },
                'allocation': {
                    'cash': 0.50,
                    'gold': 0.20,
                    'bonds': 0.20,
                    'equities': 0.10
                },
                'expected_return': 0.00,
                'max_drawdown': -0.50,
                'description': 'Systemic crisis or market crash'
            },
            
            'STAGFLATION': {
                'conditions': {
                    'gdp_growth': (-0.02, 0.01),
                    'inflation': (0.05, 0.15),
                    'unemployment': (0.06, 0.10)
                },
                'allocation': {
                    'commodities': 0.30,
                    'gold': 0.30,
                    'cash': 0.20,
                    'bonds': 0.20
                },
                'expected_return': 0.06,
                'max_drawdown': -0.20,
                'description': 'Stagnant growth with high inflation'
            },
            
            'MELT_UP': {
                'conditions': {
                    'gdp_growth': (0.04, 0.08),
                    'vix': (15, 30),
                    'inflation': (0.02, 0.04)
                },
                'allocation': {
                    'equities': 0.85,
                    'gold': 0.10,
                    'cash': 0.05
                },
                'expected_return': 0.20,
                'max_drawdown': -0.30,
                'description': 'Euphoric market rally'
            },
            
            'RECOVERY': {
                'conditions': {
                    'gdp_growth': (0.01, 0.03),
                    'unemployment': (0.04, 0.07),
                    'vix': (18, 30)
                },
                'allocation': {
                    'equities': 0.60,
                    'bonds': 0.30,
                    'gold': 0.10
                },
                'expected_return': 0.10,
                'max_drawdown': -0.18,
                'description': 'Post-crisis recovery phase'
            },
            
            'TAPER_TANTRUM': {
                'conditions': {
                    'fed_rate': (0.04, 0.07),
                    'credit_spread': (0.02, 0.05),
                    'vix': (20, 35)
                },
                'allocation': {
                    'cash': 0.40,
                    'bonds': 0.40,
                    'gold': 0.20
                },
                'expected_return': 0.03,
                'max_drawdown': -0.12,
                'description': 'Market shock from Fed tightening'
            },
            
            'GEOPOLITICAL_SHOCK': {
                'conditions': {
                    'vix': (30, 60),
                    'dxy': (105, 120),
                    'credit_spread': (0.02, 0.06)
                },
                'allocation': {
                    'gold': 0.35,
                    'cash': 0.35,
                    'bonds': 0.20,
                    'equities': 0.10
                },
                'expected_return': 0.05,
                'max_drawdown': -0.20,
                'description': 'War, sanctions, or major geopolitical event'
            },
            
            'TECH_DISRUPTION': {
                'conditions': {
                    'gdp_growth': (0.03, 0.06),
                    'inflation': (0.00, 0.02),
                    'vix': (12, 22)
                },
                'allocation': {
                    'equities': 0.75,
                    'bonds': 0.15,
                    'gold': 0.10
                },
                'expected_return': 0.15,
                'max_drawdown': -0.22,
                'description': 'AI/tech revolution driving markets'
            },
            
            'DEGLOBALIZATION': {
                'conditions': {
                    'inflation': (0.03, 0.06),
                    'dxy': (100, 110),
                    'credit_spread': (0.015, 0.035)
                },
                'allocation': {
                    'equities': 0.40,
                    'commodities': 0.30,
                    'gold': 0.20,
                    'cash': 0.10
                },
                'expected_return': 0.08,
                'max_drawdown': -0.18,
                'description': 'Supply chain reorganization era'
            }
        }
    
    def detect_regime(self, market_data: Dict) -> Dict:
        """
        Detects current market regime based on parameters
        
        Args:
            market_data: Dictionary with current market parameters
            
        Returns:
            Dictionary with regime, confidence, and allocation
        """
        scores = {}
        
        for regime_name, regime_def in self.regimes.items():
            conditions = regime_def['conditions']
            matches = 0
            total = len(conditions)
            
            for param, (low, high) in conditions.items():
                if param in market_data:
                    value = market_data[param]
                    if low <= value <= high:
                        matches += 1
            
            score = matches / total if total > 0 else 0.0
            scores[regime_name] = score
        
        # Best match
        best_regime = max(scores, key=scores.get)
        confidence = scores[best_regime]
        
        regime_info = self.regimes[best_regime]
        
        result = {
            'regime': best_regime,
            'confidence': round(confidence, 3),
            'allocation': regime_info['allocation'],
            'expected_return': regime_info['expected_return'],
            'max_drawdown': regime_info['max_drawdown'],
            'description': regime_info['description'],
            'all_scores': {k: round(v, 3) for k, v in scores.items()}
        }
        
        logger.info(f"Detected regime: {best_regime} (confidence: {confidence:.3f})")
        
        return result
    
    def calculate_lsi(self, market_data: Dict) -> Dict:
        """
        Calculates Liquidity Stress Index (0-100)
        
        Args:
            market_data: Dictionary with market parameters
            
        Returns:
            Dictionary with LSI score and status
        """
        components = {}
        
        # Component 1: VIX (30% weight)
        vix = market_data.get('vix', 20)
        vix_component = min((vix - 15) / 35 * 100, 100)
        components['vix'] = vix_component * 0.30
        
        # Component 2: Credit spreads (25% weight)
        spread = market_data.get('credit_spread', 0.015)
        spread_component = min(spread / 0.05 * 100, 100)
        components['credit_spread'] = spread_component * 0.25
        
        # Component 3: Dollar stress (20% weight)
        dxy = market_data.get('dxy', 100)
        dxy_component = max((dxy - 95) / 15 * 100, 0)
        components['dxy_stress'] = dxy_component * 0.20
        
        # Component 4: Baseline/Other factors (25% weight)
        # This captures general market stress not in other components
        components['baseline'] = 25 * 0.25
        
        # Total LSI
        lsi = sum(components.values())
        
        # Status interpretation
        if lsi >= 75:
            status = 'CRITICAL_LIQUIDITY_SHOCK'
        elif lsi >= 50:
            status = 'SEVERE_STRESS'
        elif lsi >= 30:
            status = 'MODERATE_STRESS'
        else:
            status = 'NORMAL'
        
        result = {
            'lsi': round(lsi, 2),
            'status': status,
            'components': {k: round(v, 2) for k, v in components.items()}
        }
        
        logger.info(f"LSI: {lsi:.2f} ({status})")
        
        return result
    
    def get_regime_info(self, regime_name: str) -> Dict:
        """Returns detailed information about a specific regime"""
        return self.regimes.get(regime_name, {})
    
    def list_all_regimes(self) -> Dict:
        """Returns all regime definitions"""
        return self.regimes
